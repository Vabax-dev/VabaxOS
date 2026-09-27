// SPDX-FileCopyrightText: 2026 Vabax and VabaxOS contributors
// SPDX-License-Identifier: GPL-3.0-or-later
//
// The Start button and the search box of the taskbar (block 15, ADR-0025,
// Vabax's choice C: the VabaxOS Start menu for everyone, ArcMenu removed).
// As in Windows 11, at the left of the taskbar:
//   - "Start", with the VabaxOS logo: a click opens or closes the menu;
//   - a search box: a click opens the menu in its search field, and what is
//     written in the box goes to the menu's search, which opens with it.
// Both have a written name, so Orca reads them (Super+T, Ctrl+Alt+Tab).
// The keyboard keeps Super and Super+S (vabaxos-keys).

import Clutter from 'gi://Clutter';
import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import St from 'gi://St';

import * as Main from 'resource:///org/gnome/shell/ui/main.js';

const LOGO = '/usr/share/icons/hicolor/scalable/apps/vabaxos-logo.svg';
// Letters written quickly go to the menu together.
const TYPING_MS = 250;

// GNOME Shell 50 names actors with accessible_name; older ones only
// through their Atk object (the headless test may run GNOME Shell 46).
function setAccessibleName(actor, name) {
    const accessible = actor.get_accessible?.();
    if (accessible?.set_name)
        accessible.set_name(name);
    else
        actor.accessible_name = name;
}

export class TaskbarStart {
    constructor(gettext, toggleStart) {
        this._ = gettext;
        this._toggleStart = toggleStart;
        this._boxes = [];
        this._typingId = 0;
        this._panelsId = 0;
    }

    enable() {
        // Dash to Panel makes its panels again when monitors or its settings
        // change: the button goes back on each new panel.
        if (global.dashToPanel?.connect)
            this._panelsId = global.dashToPanel.connect('panels-created', () => this._addToPanels());
        this._addToPanels();
    }

    disable() {
        if (this._panelsId && global.dashToPanel)
            global.dashToPanel.disconnect(this._panelsId);
        this._panelsId = 0;
        if (this._typingId)
            GLib.source_remove(this._typingId);
        this._typingId = 0;
        this._removeBoxes();
    }

    _removeBoxes() {
        for (const box of this._boxes)
            box.destroy();
        this._boxes = [];
    }

    _addToPanels() {
        this._removeBoxes();
        const panels = global.dashToPanel?.panels ?? [];
        const leftBoxes = panels.length > 0 ? panels.map(p => p._leftBox) : [Main.panel._leftBox];
        for (const leftBox of leftBoxes.filter(b => b)) {
            const box = this._makeBox();
            box.connect('destroy', () => {
                this._boxes = this._boxes.filter(b => b !== box);
            });
            leftBox.insert_child_at_index(box, 0);
            this._boxes.push(box);
        }
    }

    _makeBox() {
        const _ = this._;
        const box = new St.BoxLayout({style_class: 'vabaxos-taskbar-start', y_align: Clutter.ActorAlign.CENTER});

        const button = new St.Button({
            style_class: 'panel-button',
            can_focus: true,
            reactive: true,
            track_hover: true,
            accessible_name: _('Start'),
            y_align: Clutter.ActorAlign.FILL,
        });
        const inner = new St.BoxLayout({style: 'spacing: 6px;'});
        inner.add_child(new St.Icon({
            gicon: Gio.icon_new_for_string(LOGO),
            style_class: 'system-status-icon',
            y_align: Clutter.ActorAlign.CENTER,
        }));
        inner.add_child(new St.Label({text: _('Start'), y_align: Clutter.ActorAlign.CENTER}));
        button.set_child(inner);
        button.connect('clicked', () => this._toggleStart());
        box.add_child(button);

        const search = new St.Entry({
            hint_text: _('Search'),
            can_focus: true,
            reactive: true,
            track_hover: true,
            accessible_name: _('Search programs, settings and files'),
            style: 'width: 13em; margin: 4px 6px; border-radius: 16px;',
            y_align: Clutter.ActorAlign.CENTER,
        });
        search.set_primary_icon(new St.Icon({icon_name: 'system-search-symbolic', style_class: 'popup-menu-icon'}));
        // A click opens the menu in its search field, as in Windows 11.
        search.connect('button-press-event', () => {
            this._openSearch('');
            return Clutter.EVENT_STOP;
        });
        // The keyboard focus goes to the text inside the box: it needs the
        // name too (in GNOME Shell the box itself is a panel for AT-SPI).
        const text = search.clutter_text;
        setAccessibleName(text, _('Search programs, settings and files'));
        text.connect('text-changed', () => {
            if (this._typingId)
                GLib.source_remove(this._typingId);
            this._typingId = GLib.timeout_add(GLib.PRIORITY_DEFAULT, TYPING_MS, () => {
                this._typingId = 0;
                const written = search.get_text();
                if (written) {
                    search.set_text('');
                    this._openSearch(written);
                }
                return GLib.SOURCE_REMOVE;
            });
        });
        text.connect('activate', () => {
            const written = search.get_text();
            search.set_text('');
            this._openSearch(written);
        });
        box.add_child(search);
        return box;
    }

    // The menu opens with the text in its search field (vabaxos-start
    // --search); the menu's window then takes the focus (vabaxos-keys).
    _openSearch(written) {
        if (global.stage.get_key_focus())
            global.stage.set_key_focus(null);
        try {
            Gio.Subprocess.new(['vabaxos-start', '--search', written], Gio.SubprocessFlags.NONE);
        } catch (e) {
            logError(e, 'VabaxOS: cannot open the Start menu');
            this._toggleStart();
        }
    }
}
