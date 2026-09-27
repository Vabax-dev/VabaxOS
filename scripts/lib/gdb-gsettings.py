"""gdb script: which settings meet in the GJS and GSettings deadlock.

GNOME Shell froze at startup (2026-09-26): its main thread, collecting
JavaScript garbage while holding the GJS toggle queue lock, freed a
GSettings object and waited for the lock of the GSettings backend; the
dconf worker thread, holding that lock while it told every GSettings
object about a change, took a reference to a JavaScript-owned one and
waited for the toggle queue. This prints, for each thread in the frames
of that code, the arguments and local variables, and the schema and path
of the GSettings objects involved: which object was freed and which
change arrived. Used by test-boot.sh with gdb -x.
"""

import gdb

FRAMES = {
    "g_settings_backend_watch_weak_notify": "where_the_object_was",
    "g_settings_backend_dispatch_signal": None,
    "g_settings_backend_changed": None,
    "g_settings_backend_path_changed": None,
    "g_settings_backend_keys_changed": None,
    "dconf_settings_backend_changed": None,
    "g_settings_finalize": "object",
}


def settings_name(expression):
    try:
        priv = gdb.parse_and_eval(f"((GSettings *) {expression})->priv")
        return f"{priv['schema_id'].string()} {priv['path'].string()}"
    except (gdb.error, UnicodeDecodeError) as error:
        return f"? ({error})"


for thread in gdb.selected_inferior().threads():
    thread.switch()
    frame = gdb.newest_frame()
    while frame is not None:
        name = frame.name() or ""
        if name in FRAMES:
            frame.select()
            print(f"GSDIAG thread {thread.num} ({thread.name}): {name}")
            for command in ("info args", "info locals"):
                try:
                    gdb.execute(command)
                except gdb.error as error:
                    print(f"GSDIAG {command}: {error}")
            if FRAMES[name]:
                print(f"GSDIAG settings: {settings_name(FRAMES[name])}")
            if name == "g_settings_backend_dispatch_signal":
                print(f"GSDIAG watch target: {settings_name('watch->target_ptr')}")
        frame = frame.older()
