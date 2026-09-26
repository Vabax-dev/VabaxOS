// SPDX-FileCopyrightText: 2026 Vabax and VabaxOS contributors
// SPDX-License-Identifier: GPL-3.0-or-later
//
// VabaxOS keys (block 8): the Windows keys that GNOME has no setting for.
// The others (Super+A, Super+N, Super+D, Super+E, Super+I, Alt+Tab...)
// are plain GNOME settings in /etc/dconf/db/vabaxos.d/30-windows-keys.
//
//   Super+T     the taskbar: the first program, again for the next one
//   Super+B     the notification area: program icons, clock, network,
//               volume, battery; again for the next one
//   Super       the VabaxOS Start menu (vabaxos-start, block 12): search,
//               and categories opened with the arrows; again, it closes
//   Super+S     the Start menu, to search: the same as Super alone
//   Super+Down  a maximized or tiled window goes back to its size,
//               any other window is minimized
//   Super+Alt+D where am I: program, window, desktop, open windows (said
//               by Orca through its D-Bus service, or a notification)
//   Alt+F4      closes the window; on the desktop or the taskbar asks to
//               shut down, as in Windows (the desktop takes the focus when
//               the last window closes)
//
// A new window takes the focus even when it was started without a GNOME
// "activation token" (from a terminal, a script, a program that opens a
// second window): instead of the "is ready" notification, which a blind
// user cannot find (block 11). Only in its first seconds: a window that
// asks for attention later (a new e-mail) does not steal the focus.
//
// The focus moves with the keyboard focus of GNOME Shell, as Ctrl+Alt+Tab
// does, so Orca reads it; then the arrows move, Enter opens and Escape goes
// back to the window.
//
// The Start button and the search box of the taskbar are in taskbarStart.js
// (block 15).

import Clutter from 'gi://Clutter';
import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import GObject from 'gi://GObject';
import Meta from 'gi://Meta';
import Shell from 'gi://Shell';
import St from 'gi://St';

import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import * as Util from 'resource:///org/gnome/shell/misc/util.js';
import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';

import {TaskbarStart} from './taskbarStart.js';

const KEYS = ['focus-taskbar', 'focus-tray', 'open-start-menu', 'minimize-or-restore', 'where-am-i'];
const NEW_WINDOW_MS = 8000;

export default class VabaxOSKeys extends Extension {
    enable() {
        this._settings = this.getSettings();
        const handlers = {
            'focus-taskbar': () => this._focusTaskbar(),
            'focus-tray': () => this._focusTray(),
            'open-start-menu': () => this._toggleStart(),
            'minimize-or-restore': () => this._minimizeOrRestore(),
            'where-am-i': () => this._whereAmI(),
        };
        for (const key of KEYS) {
            Main.wm.addKeybinding(key, this._settings, Meta.KeyBindingFlags.NONE,
                Shell.ActionMode.NORMAL | Shell.ActionMode.OVERVIEW, handlers[key]);
        }
        // Super alone: GNOME's handler (the overview) is blocked, ours opens
        // the Start menu, as ArcMenu does with its own.
        this._overlayDefault = GObject.signal_handler_find(global.display, {signalId: 'overlay-key'});
        if (this._overlayDefault)
            GObject.signal_handler_block(global.display, this._overlayDefault);
        this._overlayId = global.display.connect('overlay-key', () => this._toggleStart());
        Main.wm.allowKeybinding('overlay-key', Shell.ActionMode.NORMAL | Shell.ActionMode.OVERVIEW |
            Shell.ActionMode.POPUP);
        Main.wm.setCustomKeybindingHandler('close', Shell.ActionMode.NORMAL,
            (display, window) => this._close(window));
        this._createdId = global.display.connect('window-created', (display, window) => {
            window._vabaxosCreated = GLib.get_monotonic_time() / 1000;
        });
        this._attentionIds = ['window-demands-attention', 'window-marked-urgent'].map(signal =>
            global.display.connect(signal, (display, window) => this._newWindowAttention(window)));
        // When GNOME Shell has the keyboard (the taskbar after Super+T),
        // Alt+F4 reaches its stage: ask to shut down, as Windows does.
        this._stageKeyId = global.stage.connect('key-press-event',
            (actor, event) => this._onStageKey(event));
        // With no window focused, keys go nowhere. As in Windows, the
        // desktop takes the focus when the last window closes: Orca reads
        // its icons, and Alt+F4 there asks to shut down.
        this._focusId = global.display.connect('notify::focus-window', () => {
            if (!global.display.focus_window && !this._focusIdle) {
                this._focusIdle = GLib.idle_add(GLib.PRIORITY_DEFAULT, () => {
                    this._focusIdle = 0;
                    this._focusDesktop();
                    return GLib.SOURCE_REMOVE;
                });
            }
        });
        this._taskbarStart = new TaskbarStart(this.gettext.bind(this), () => this._toggleStart());
        this._taskbarStart.enable();
    }

    disable() {
        this._taskbarStart.disable();
        this._taskbarStart = null;
        for (const key of KEYS)
            Main.wm.removeKeybinding(key);
        Meta.keybindings_set_custom_handler('close', null);
        global.display.disconnect(this._overlayId);
        if (this._overlayDefault)
            GObject.signal_handler_unblock(global.display, this._overlayDefault);
        Main.wm.allowKeybinding('overlay-key', Shell.ActionMode.NORMAL | Shell.ActionMode.OVERVIEW);
        global.stage.disconnect(this._stageKeyId);
        global.display.disconnect(this._focusId);
        global.display.disconnect(this._createdId);
        this._attentionIds.forEach(id => global.display.disconnect(id));
        if (this._focusIdle) {
            GLib.source_remove(this._focusIdle);
            this._focusIdle = 0;
        }
        this._settings = null;
    }

    // The panel of Dash to Panel on the main screen, or GNOME's top bar.
    // Dash to Panel's panels, the main screen first, only those on screen:
    // after Dash to Panel makes its panels again an old one may still be in
    // its list (CI of block 15, 2026-09-26: Super+T found no program there).
    _panels() {
        const panels = (global.dashToPanel?.panels ?? []).filter(p => p.panel?.mapped ?? true);
        return [...panels.filter(p => p.isPrimary), ...panels.filter(p => !p.isPrimary)];
    }

    _panel() {
        return this._panels()[0] ?? null;
    }

    _focused(actor) {
        const focus = global.stage.get_key_focus();
        return focus && actor.contains(focus) ? focus : null;
    }

    _focusTaskbar() {
        let icons = [];
        for (const panel of this._panels()) {
            icons = (panel.taskbar?._getAppIcons?.() ?? []).filter(icon => icon.mapped);
            if (icons.length > 0)
                break;
        }
        if (icons.length === 0) {
            this._focusIn(this._panel()?._leftBox ?? Main.panel);
            return;
        }
        const index = icons.findIndex(icon => this._focused(icon));
        icons[(index + 1) % icons.length].grab_key_focus();
    }

    _focusTray() {
        this._focusIn(this._panel()?._rightBox ?? Main.panel._rightBox);
    }

    // The first control in box, or the next one if the focus is already there.
    _focusIn(box) {
        const focus = this._focused(box);
        if (!focus || !box.navigate_focus(focus, St.DirectionType.TAB_FORWARD, false))
            box.navigate_focus(null, St.DirectionType.TAB_FORWARD, false);
    }

    _isDesktop(window) {
        // Desktop Icons NG marks its windows with customJS_ding, and titles
        // its desktop window "Desktop Icons <n>" (its emulateX11WindowType.js).
        return window.get_window_type() === Meta.WindowType.DESKTOP || Boolean(window.customJS_ding) ||
            (window.get_title() ?? '').startsWith('Desktop Icons ');
    }

    _unmaximize(window) {
        try {
            window.unmaximize();
        } catch {
            window.unmaximize(Meta.MaximizeFlags.BOTH);
        }
    }

    _minimizeOrRestore() {
        const window = global.display.focus_window;
        if (!window || this._isDesktop(window))
            return;
        const rect = window.untiledRect; // set by Tiling Assistant on its tiles
        if (rect) {
            if (window.is_maximized())
                this._unmaximize(window);
            window.move_resize_frame(false, rect.x, rect.y, rect.width, rect.height);
            window.isTiled = false;
            window.tiledRect = null;
            window.untiledRect = null;
        } else if (window.is_maximized()) {
            this._unmaximize(window);
        } else if (window.can_minimize()) {
            window.minimize();
        }
    }

    // The Start menu: opened by GNOME Shell, which gives it the focus
    // (an activation token); Super again, or on its window, closes it.
    _toggleStart() {
        const app = Shell.AppSystem.get_default().lookup_app('org.vabaxos.Start.desktop');
        if (!app) {
            Main.overview.toggle();
            return;
        }
        const focus = global.display.focus_window;
        if (focus && Shell.WindowTracker.get_default().get_window_app(focus) === app) {
            focus.delete(global.get_current_time());
            return;
        }
        if (Main.overview.visible)
            Main.overview.hide();
        app.activate();
    }

    _newWindowAttention(window) {
        // The Start menu runs hidden from the login: when it shows (the
        // search box of the taskbar starts it with --search), it asks for
        // attention, and it is always the user's request.
        const isStart = Shell.WindowTracker.get_default().get_window_app(window)?.get_id() ===
            'org.vabaxos.Start.desktop';
        const created = window._vabaxosCreated;
        if (!isStart && (created === undefined || GLib.get_monotonic_time() / 1000 - created > NEW_WINDOW_MS))
            return;
        if (Main.modalCount > 0 || this._isDesktop(window))
            return;
        Main.activateWindow(window);
    }

    _whereAmI() {
        const _ = this.gettext.bind(this);
        const window = global.display.focus_window;
        const parts = [];
        if (window && !this._isDesktop(window)) {
            const app = Shell.WindowTracker.get_default().get_window_app(window);
            const title = window.get_title() || '';
            const name = app ? app.get_name() : '';
            parts.push(name && !title.includes(name) ? `${name}: ${title}` : title);
        } else {
            parts.push(_('Desktop'));
        }
        const manager = global.workspace_manager;
        if (manager.get_n_workspaces() > 1) {
            parts.push(_('desktop %d of %d').format(manager.get_active_workspace_index() + 1,
                manager.get_n_workspaces()));
        }
        const windows = global.display.get_tab_list(Meta.TabList.NORMAL, null).filter(w => !this._isDesktop(w));
        parts.push(windows.length === 1 ? _('1 window open') : _('%d windows open').format(windows.length));
        this._speak(parts.filter(p => p).join('. '));
    }

    // Orca says it at once; without Orca, a notification.
    _speak(text) {
        Gio.DBus.session.call('org.gnome.Orca.Service', '/org/gnome/Orca/Service', 'org.gnome.Orca.Service',
            'PresentMessage', new GLib.Variant('(s)', [text]), null, Gio.DBusCallFlags.NONE, 2000, null,
            (connection, result) => {
                try {
                    connection.call_finish(result);
                } catch {
                    Main.notify(this.gettext('Where am I'), text);
                }
            });
    }

    _focusDesktop() {
        if (global.display.focus_window || Main.modalCount > 0)
            return;
        // Not global.get_window_actors(): Desktop Icons NG hides its window there.
        const windows = global.display.list_all_windows();
        const desktop = windows.find(w => (w.get_title() ?? '').startsWith('Desktop Icons ')) ??
            windows.find(w => this._isDesktop(w));
        desktop?.activate(global.get_current_time());
    }

    _onStageKey(event) {
        const altF4 = event.get_key_symbol() === Clutter.KEY_F4 &&
            (event.get_state() & Clutter.ModifierType.MOD1_MASK) !== 0;
        const window = global.display.focus_window;
        if (!altF4 || (window && !this._isDesktop(window)) || Main.modalCount > 0)
            return Clutter.EVENT_PROPAGATE;
        Util.spawn(['gnome-session-quit', '--power-off']);
        return Clutter.EVENT_STOP;
    }

    _close(window) {
        if (window && !this._isDesktop(window)) {
            if (window.can_close())
                window.delete(global.get_current_time());
            return;
        }
        Util.spawn(['gnome-session-quit', '--power-off']);
    }
}
