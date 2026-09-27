// Reproduces the GJS 1.88.1 deadlock that froze GNOME Shell at startup in
// VabaxOS (2026-09-27; the same code is in GJS's master branch).
//
// The main thread, sweeping JavaScript wrappers after a garbage collection
// with the toggle queue locked (update_heap_wrapper_weak_pointers), frees a
// GSettings object whose wrapper had a signal handler (a toggle reference)
// and waits for the GSettings backend lock in its weak notify. The dconf
// worker thread holds that lock while it tells every GSettings object about
// a change written by another process (g_settings_backend_dispatch_signal),
// takes a reference to a JavaScript-owned one (g_weak_ref_get, a toggle up)
// and spins on the toggle queue lock.
//
//     gjs tests/upstream/gjs-gsettings-deadlock.js
//
// with another process changing a watched key, for example
//     while :; do gsettings set org.gnome.desktop.interface cursor-size $((24 + RANDOM % 8)); done
// Prints "round N" lines; they stop within seconds when it deadlocks (the
// dconf worker thread then uses a whole CPU).
const {Gio, GLib} = imports.gi;
const System = imports.system;

let rounds = 0;
let keep = [];
GLib.timeout_add(GLib.PRIORITY_DEFAULT, 1, () => {
    for (let i = 0; i < 100; i++) {
        const settings = new Gio.Settings({schema_id: 'org.gnome.desktop.interface'});
        settings.connect('changed::cursor-size', () => {});
        keep.push(settings);
    }
    if (keep.length > 600)
        keep = [];
    System.gc();
    rounds++;
    if (rounds % 10 === 0)
        print(`round ${rounds}`);
    return GLib.SOURCE_CONTINUE;
});
new GLib.MainLoop(null, false).run();
