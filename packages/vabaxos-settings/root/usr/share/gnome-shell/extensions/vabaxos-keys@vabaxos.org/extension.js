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
//   Super+Alt+R the text of the window in use, recognized (OCR) by
//               vabaxos-ocr and shown as plain text for Orca, like NVDA+R;
//               Super+Alt+Shift+R the whole screen. The picture can only
//               be taken here: GNOME Shell refuses its screenshot service
//               to other programs.
//   Super+H     dictation, as in Windows: vabaxos-dictation listens; Super+H
//               again, and the text is written where the cursor is, the way
//               the screen keyboard of GNOME writes (the input method, or
//               key presses for programs without one), then said aloud.
//   Alt+F4      closes the window; on the desktop or the taskbar asks to
//               shut down, as in Windows (the desktop takes the focus when
//               the last window closes)
//
// The Start button on the taskbar (ADR-0025, accepted by Vabax on
// 2026-11-01): the VabaxOS logo and the word "Start", at the left; a click,
// Enter or Space opens the VabaxOS Start menu, as Super does. ArcMenu is no
// longer installed.
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

import Atk from 'gi://Atk';
import Clutter from 'gi://Clutter';
import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import GObject from 'gi://GObject';
import Meta from 'gi://Meta';
import Shell from 'gi://Shell';
import St from 'gi://St';

import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import * as PanelMenu from 'resource:///org/gnome/shell/ui/panelMenu.js';
import * as Util from 'resource:///org/gnome/shell/misc/util.js';
import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';

const LOGO = '/usr/share/icons/hicolor/scalable/apps/vabaxos-logo.svg';

// A plain button, not a menu: Orca says "Start, button". The key and click
// signals of the actor work with every GNOME Shell 50 version (the menu
// gestures of PanelMenu.Button changed between versions).
const StartButton = GObject.registerClass(
class StartButton extends PanelMenu.Button {
    _init(label, onActivate) {
        super._init(0.0, label, true);
        this.accessible_role = Atk.Role.PUSH_BUTTON;
        this.accessible_name = label;
        const box = new St.BoxLayout({style_class: 'panel-status-menu-box'});
        if (GLib.file_test(LOGO, GLib.FileTest.EXISTS)) {
            box.add_child(new St.Icon({
                gicon: Gio.FileIcon.new(Gio.File.new_for_path(LOGO)),
                style_class: 'system-status-icon',
            }));
        }
        box.add_child(new St.Label({text: label, y_align: Clutter.ActorAlign.CENTER}));
        this.add_child(box);
        this.connect('button-release-event', (actor, event) => {
            if (event.get_button() !== Clutter.BUTTON_PRIMARY)
                return Clutter.EVENT_PROPAGATE;
            onActivate();
            return Clutter.EVENT_STOP;
        });
        this.connect('touch-event', (actor, event) => {
            if (event.type() !== Clutter.EventType.TOUCH_END)
                return Clutter.EVENT_PROPAGATE;
            onActivate();
            return Clutter.EVENT_STOP;
        });
        this.connect('key-press-event', (actor, event) => {
            const key = event.get_key_symbol();
            if (key !== Clutter.KEY_Return && key !== Clutter.KEY_KP_Enter && key !== Clutter.KEY_space)
                return Clutter.EVENT_PROPAGATE;
            onActivate();
            return Clutter.EVENT_STOP;
        });
    }
});

const KEYS = ['focus-taskbar', 'focus-tray', 'open-start-menu', 'minimize-or-restore', 'where-am-i',
    'recognize-window', 'recognize-screen', 'dictation'];

Gio._promisify(Shell.Screenshot.prototype, 'screenshot');
Gio._promisify(Shell.Screenshot.prototype, 'screenshot_window');
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
            'recognize-window': () => this._recognize(false),
            'recognize-screen': () => this._recognize(true),
            'dictation': () => this._dictation(),
        };
        for (const key of KEYS) {
            Main.wm.addKeybinding(key, this._settings, Meta.KeyBindingFlags.NONE,
                Shell.ActionMode.NORMAL | Shell.ActionMode.OVERVIEW, handlers[key]);
        }
        // Super alone: GNOME's handler (the overview) is blocked, ours opens
        // the Start menu.
        this._overlayDefault = GObject.signal_handler_find(global.display, {signalId: 'overlay-key'});
        if (this._overlayDefault)
            GObject.signal_handler_block(global.display, this._overlayDefault);
        this._overlayId = global.display.connect('overlay-key', () => this._toggleStart());
        Main.wm.allowKeybinding('overlay-key', Shell.ActionMode.NORMAL | Shell.ActionMode.OVERVIEW |
            Shell.ActionMode.POPUP);
        this._startButton = new StartButton(this.gettext('Start'), () => this._toggleStart());
        Main.panel.addToStatusArea('vabaxos-start', this._startButton, 0, 'left');
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
    }

    disable() {
        for (const key of KEYS)
            Main.wm.removeKeybinding(key);
        this._startButton?.destroy();
        this._startButton = null;
        if (this._dictating)
            this._run(['vabaxos-dictation', 'cancel']);
        this._dictating = false;
        this._keyboard?.run_dispose();
        this._keyboard = null;
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
        const created = window._vabaxosCreated;
        if (created === undefined || GLib.get_monotonic_time() / 1000 - created > NEW_WINDOW_MS)
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

    // A picture of the window in use, or of the screen, for vabaxos-ocr.
    async _recognize(wholeScreen) {
        const _ = this.gettext.bind(this);
        if (!GLib.find_program_in_path('vabaxos-ocr')) {
            this._speak(_('Text recognition is not installed.'));
            return;
        }
        const window = global.display.focus_window;
        const useWindow = !wholeScreen && window && !this._isDesktop(window);
        this._speak(_('Recognizing the text.'));
        try {
            const dir = GLib.build_filenamev([GLib.get_user_runtime_dir(), 'vabaxos-ocr']);
            GLib.mkdir_with_parents(dir, 0o700);
            const path = GLib.build_filenamev([dir, `${GLib.get_monotonic_time()}.png`]);
            const stream = Gio.File.new_for_path(path).replace(null, false, Gio.FileCreateFlags.PRIVATE, null);
            const shooter = new Shell.Screenshot();
            if (useWindow)
                await shooter.screenshot_window(false, false, stream);
            else
                await shooter.screenshot(false, stream);
            stream.close(null);
            const title = useWindow ? window.get_title() ?? '' : _('Screen');
            Util.spawn(['vabaxos-ocr', '--title', title, path]);
        } catch (e) {
            logError(e, 'vabaxos-keys: text recognition');
            this._speak(_('Text recognition failed.'));
        }
    }

    // Runs a program; resolves with [exit status, standard output].
    _run(argv) {
        return new Promise(resolve => {
            try {
                const process = Gio.Subprocess.new(argv,
                    Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_SILENCE);
                process.communicate_utf8_async(null, null, (proc, result) => {
                    try {
                        const [, stdout] = proc.communicate_utf8_finish(result);
                        resolve([proc.get_exit_status(), stdout ?? '']);
                    } catch {
                        resolve([-1, '']);
                    }
                });
            } catch {
                resolve([-1, '']);
            }
        });
    }

    async _dictation() {
        const _ = this.gettext.bind(this);
        if (!GLib.find_program_in_path('vabaxos-dictation')) {
            this._speak(_('Dictation is not installed.'));
            return;
        }
        if (this._dictatingBusy)
            return;
        this._dictatingBusy = true;
        try {
            if (!this._dictating) {
                const [status] = await this._run(['vabaxos-dictation', 'start']);
                this._dictating = status === 0;
                if (!this._dictating)
                    this._speak(_('Dictation cannot start.'));
                return;
            }
            this._dictating = false;
            const [status, text] = await this._run(['vabaxos-dictation', 'stop']);
            if (status === 3) {
                this._speak(_('Nothing heard.'));
            } else if (status !== 0 || !text.trim()) {
                this._speak(_('Dictation failed.'));
            } else {
                this._type(text.replace(/\n$/, ''));
                this._speak(text.trim());
            }
        } finally {
            this._dictatingBusy = false;
        }
    }

    // Writes text where the focus is, as GNOME's screen keyboard does: through
    // the input method when the program has one, else with key presses.
    _type(text) {
        const lines = text.split('\n');
        lines.forEach((line, i) => {
            if (i > 0)
                this._key(Clutter.KEY_Return);
            if (!line)
                return;
            if (Main.inputMethod.currentFocus) {
                Main.inputMethod.commit(line);
            } else {
                for (const char of line)
                    this._key(Clutter.unicode_to_keysym(char.codePointAt(0)));
            }
        });
    }

    _key(keyval) {
        if (!this._keyboard) {
            const seat = Clutter.get_default_backend().get_default_seat();
            this._keyboard = seat.create_virtual_device(Clutter.InputDeviceType.KEYBOARD_DEVICE);
        }
        const time = Clutter.get_current_event_time() * 1000;
        this._keyboard.notify_keyval(time, keyval, Clutter.KeyState.PRESSED);
        this._keyboard.notify_keyval(time, keyval, Clutter.KeyState.RELEASED);
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
