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
//   Super+S     the Start menu, to search: the same as Super alone
//   Super+Down  a maximized or tiled window goes back to its size,
//               any other window is minimized
//   Alt+F4      closes the window; on the desktop or the taskbar asks to
//               shut down, as in Windows (the desktop takes the focus when
//               the last window closes)
//
// The focus moves with the keyboard focus of GNOME Shell, as Ctrl+Alt+Tab
// does, so Orca reads it; then the arrows move, Enter opens and Escape goes
// back to the window.

import Clutter from 'gi://Clutter';
import GLib from 'gi://GLib';
import Meta from 'gi://Meta';
import Shell from 'gi://Shell';
import St from 'gi://St';

import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import * as Util from 'resource:///org/gnome/shell/misc/util.js';
import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';

const KEYS = ['focus-taskbar', 'focus-tray', 'open-start-menu', 'minimize-or-restore'];

export default class VabaxOSKeys extends Extension {
    enable() {
        this._settings = this.getSettings();
        const handlers = {
            'focus-taskbar': () => this._focusTaskbar(),
            'focus-tray': () => this._focusTray(),
            // What Super alone does: ArcMenu listens to this signal.
            'open-start-menu': () => global.display.emit('overlay-key'),
            'minimize-or-restore': () => this._minimizeOrRestore(),
        };
        for (const key of KEYS) {
            Main.wm.addKeybinding(key, this._settings, Meta.KeyBindingFlags.NONE,
                Shell.ActionMode.NORMAL | Shell.ActionMode.OVERVIEW, handlers[key]);
        }
        Main.wm.setCustomKeybindingHandler('close', Shell.ActionMode.NORMAL,
            (display, window) => this._close(window));
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
    }

    disable() {
        for (const key of KEYS)
            Main.wm.removeKeybinding(key);
        Meta.keybindings_set_custom_handler('close', null);
        global.stage.disconnect(this._stageKeyId);
        global.display.disconnect(this._focusId);
        if (this._focusIdle) {
            GLib.source_remove(this._focusIdle);
            this._focusIdle = 0;
        }
        this._settings = null;
    }

    // The panel of Dash to Panel on the main screen, or GNOME's top bar.
    _panel() {
        const panels = global.dashToPanel?.panels ?? [];
        return panels.find(p => p.isPrimary) ?? panels[0] ?? null;
    }

    _focused(actor) {
        const focus = global.stage.get_key_focus();
        return focus && actor.contains(focus) ? focus : null;
    }

    _focusTaskbar() {
        const icons = this._panel()?.taskbar?._getAppIcons?.() ?? [];
        if (icons.length === 0) {
            this._focusIn(Main.panel);
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
        // Desktop Icons NG marks its window with customJS_ding.
        return window.get_window_type() === Meta.WindowType.DESKTOP || Boolean(window.customJS_ding);
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

    _focusDesktop() {
        if (global.display.focus_window || Main.modalCount > 0)
            return;
        // Not global.get_window_actors(): Desktop Icons NG hides its window there.
        const desktop = global.display.list_all_windows().find(w => this._isDesktop(w));
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
