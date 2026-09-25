// VabaxOS button names (ADR-0022).
//
// GNOME Shell draws some buttons with an icon and nothing else: Close and
// Expand on every notification, Collapse on a group of notifications, the
// media controls. GNOME Shell 50 gives them no accessible name, so Orca says
// only "button". This extension watches the actors of GNOME Shell and, for
// every button with neither a name nor text inside, sets a name taken from
// its icon. Buttons that already have a name are never touched.

import Atk from 'gi://Atk';
import Clutter from 'gi://Clutter';
import Gio from 'gi://Gio';
import St from 'gi://St';

import {Extension, gettext as _} from 'resource:///org/gnome/shell/extensions/extension.js';

// Widgets that are buttons for the screen reader although they are not
// St.Button: their code sets one of these roles.
const BUTTON_ROLES = new Set([Atk.Role.PUSH_BUTTON, Atk.Role.TOGGLE_BUTTON, Atk.Role.MENU_ITEM]);

// When the icon is not in the table, the style class of GNOME Shell's own
// buttons still says what they are.
const STYLE_CLASSES = {
    'message-close-button': 'window-close',
    'message-expand-button': 'notification-expand',
    'message-collapse-button': 'group-collapse',
};

// Names by icon (without "-symbolic"). Built when the extension is enabled,
// so they are in the language of the session.
function iconNames() {
    return {
        'window-close': _('Close'),
        'preview-close': _('Close'),
        'notification-expand': _('Expand'),
        'notification-collapse': _('Collapse'),
        'group-collapse': _('Collapse'),
        'media-playback-start': _('Play'),
        'media-playback-pause': _('Pause'),
        'media-playback-stop': _('Stop'),
        'media-skip-backward': _('Previous'),
        'media-skip-forward': _('Next'),
        'go-previous': _('Back'),
        'go-next': _('Forward'),
        'carousel-arrow-previous': _('Previous'),
        'carousel-arrow-next': _('Next'),
        'view-more': _('More options'),
        'open-menu': _('Menu'),
        'edit-clear': _('Clear'),
        'edit-clear-all': _('Clear all'),
        'edit-delete': _('Delete'),
        'list-add': _('Add'),
        'list-remove': _('Remove'),
        'window-minimize': _('Minimize'),
        'window-maximize': _('Maximize'),
        'window-restore': _('Restore'),
        'system-shutdown': _('Power Off'),
        'system-reboot': _('Restart'),
        'system-log-out': _('Log Out'),
        'system-lock-screen': _('Lock'),
        'emblem-system': _('Settings'),
        'preferences-system': _('Settings'),
        'applets-screenshooter': _('Take Screenshot'),
        'camera-photo': _('Take Screenshot'),
        'view-refresh': _('Refresh'),
        'edit-find': _('Search'),
        'user-trash': _('Trash'),
        'view-app-grid': _('Show Apps'),
    };
}

// Leaves: their children, if any, are drawn by GNOME Shell itself.
function isLeaf(actor) {
    return actor instanceof St.Icon || actor instanceof St.Label || actor instanceof Clutter.Text;
}

function isButton(actor) {
    return actor instanceof St.Widget &&
        (actor instanceof St.Button || BUTTON_ROLES.has(actor.accessible_role));
}

// Text inside the button: Orca reads it when the button has no name.
function hasText(actor, depth) {
    for (const child of actor.get_children()) {
        if ((child instanceof St.Label || child instanceof Clutter.Text) && child.text?.trim())
            return true;
        if (depth > 1 && hasText(child, depth - 1))
            return true;
    }
    return false;
}

function findIcon(actor, depth) {
    if (actor instanceof St.Icon)
        return actor;
    if (depth === 0)
        return null;
    for (const child of actor.get_children()) {
        const icon = findIcon(child, depth - 1);
        if (icon)
            return icon;
    }
    return null;
}

function iconNameOf(icon) {
    let name = icon.icon_name;
    if (!name && icon.gicon instanceof Gio.ThemedIcon)
        name = icon.gicon.get_names()[0];
    return name ? name.replace(/-symbolic$/, '') : null;
}

// "view-list-bullet" becomes "view list bullet": not translated, but it
// still tells more than "button" alone.
function fromIconName(name) {
    return name.split('.').pop().replace(/[-_]+/g, ' ').trim();
}

export default class ButtonNamesExtension extends Extension {
    enable() {
        this._names = iconNames();
        this._onChildAdded = (parent, child) => {
            this._visit(child);
            // An icon added to a button later, or text that now names it.
            for (let actor = parent, i = 0; actor && i < 3; actor = actor.get_parent(), i++)
                this._check(actor);
        };
        this._visit(global.stage);
    }

    disable() {
        const stack = [global.stage];
        while (stack.length) {
            const actor = stack.pop();
            if (actor._vabaxosChildAdded !== undefined) {
                actor.disconnect(actor._vabaxosChildAdded);
                delete actor._vabaxosChildAdded;
            }
            if (actor._vabaxosIconChanged !== undefined) {
                actor._vabaxosIconChanged.forEach(id => actor.disconnect(id));
                delete actor._vabaxosIconChanged;
            }
            if (actor._vabaxosNamed) {
                actor.accessible_name = null;
                delete actor._vabaxosNamed;
            }
            stack.push(...actor.get_children());
        }
        this._onChildAdded = null;
        this._names = null;
    }

    // Names the buttons under ROOT and watches for actors added later.
    _visit(root) {
        const stack = [root];
        while (stack.length) {
            const actor = stack.pop();
            if (isLeaf(actor))
                continue;
            if (actor._vabaxosChildAdded === undefined)
                actor._vabaxosChildAdded = actor.connect('child-added', this._onChildAdded);
            this._check(actor);
            stack.push(...actor.get_children());
        }
    }

    _check(actor) {
        if (!this._names || !isButton(actor))
            return;
        // A name from the code of GNOME Shell or of an extension stays.
        if (!actor._vabaxosNamed && actor.accessible_name)
            return;
        const named = !actor._vabaxosNamed &&
            ((actor instanceof St.Button && actor.label) || actor.label_actor);
        if (named || hasText(actor, 4)) {
            if (actor._vabaxosNamed) {
                actor.accessible_name = null;
                delete actor._vabaxosNamed;
            }
            return;
        }
        const name = this._nameFor(actor);
        if (name && name !== actor.accessible_name) {
            actor.accessible_name = name;
            actor._vabaxosNamed = true;
        }
    }

    _nameFor(actor) {
        const icon = findIcon(actor, 3);
        const iconName = icon ? iconNameOf(icon) : null;
        if (icon && icon._vabaxosIconChanged === undefined) {
            // Play becomes Pause, and so on: the name follows the icon.
            const recheck = () => this._check(actor);
            icon._vabaxosIconChanged = [
                icon.connect('notify::icon-name', recheck),
                icon.connect('notify::gicon', recheck),
            ];
        }
        if (iconName && this._names[iconName])
            return this._names[iconName];
        for (const [styleClass, key] of Object.entries(STYLE_CLASSES)) {
            if (actor.has_style_class_name(styleClass))
                return this._names[key];
        }
        return iconName ? fromIconName(iconName) : null;
    }
}
