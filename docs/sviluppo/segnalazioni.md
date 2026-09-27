# Segnalazioni ai progetti esterni

Decisione di Vabax (2026-09-26, risposta 13B): le segnalazioni dei difetti trovati le prepara Claude. GNOME Shell e Orca usano GitLab di GNOME, Debian usa la posta: servono account che la sessione di sviluppo non ha. Qui ci sono i testi pronti, in inglese, da incollare.

Dove si incollano:

- GNOME Shell: <https://gitlab.gnome.org/GNOME/gnome-shell/-/issues/new> (serve un account di GitLab di GNOME);
- Orca: <https://gitlab.gnome.org/GNOME/orca/-/issues/new> (stesso account);
- Debian: un messaggio di posta a `submit@bugs.debian.org`, con le prime righe esattamente come sono scritte qui sotto;
- speech-dispatcher: <https://github.com/brailcom/speechd/issues/new> (serve un account di GitHub; il repository non è fra quelli che la sessione di sviluppo può usare);
- GJS: <https://gitlab.gnome.org/GNOME/gjs/-/issues/new> (account di GitLab di GNOME).

Prima di inviare, conviene cercare se qualcuno l'ha già segnalato: il titolo, o le parole principali, nella pagina delle segnalazioni del progetto.

## 1. GNOME Shell: i pulsanti delle notifiche senza nome

**Titolo:** Notification buttons (Close, Expand, Collapse, media controls) have no accessible name

**Testo:**

> GNOME Shell 50.5 (also current main). The icon-only buttons of notifications have no accessible name, so Orca announces them as "button" only: Close and Expand on each notification banner and in the message list, Collapse on an expanded notification, and the Previous, Play/Pause and Next buttons of the media notification.
>
> Steps: enable Orca; show a notification (`notify-send Test Test`); press Super+V and move with Tab to the notification's buttons.
>
> Expected: "Close button", "Expand button" and so on. Actual: "button".
>
> The accessibility tree (for example with Accerciser) shows role "push button" and an empty name for these St.Button actors, which only have a child St.Icon. Setting `accessible_name` on them (as done for other icon-only buttons in the shell) fixes it; we ship a small extension doing that in VabaxOS (https://github.com/Vabax-dev/VabaxOS, ADR-0022) until it is fixed here.

## 2. Orca: Bloc Maiusc come tasto di Orca sotto Wayland

**Titolo:** Wayland: Caps Lock as Orca modifier toggles capitals, it is not in the key grabs

**Testo:**

> Orca 50.2, GNOME 50 on Wayland (Debian testing). With Caps Lock chosen as an Orca modifier key (desktop and laptop layout), every press of Caps Lock also toggles capital letters.
>
> With `dbus-monitor` on the session bus, Orca's `SetKeyGrabs` call to Mutter lists only the Insert keys (keysyms 65379 and 65438), not Caps Lock (65509), so Mutter does not hold back its first press. The same happens with or without DISPLAY set.
>
> Steps: set Caps Lock as the Orca modifier in Orca's preferences; press Caps Lock+T; then type a letter.
>
> Expected: Orca says the time, and letters stay lowercase. Actual: Orca says the time, and Caps Lock is now on.

## 3. Orca: la mappa della tastiera riscritta con xkbcomp sotto Wayland

**Titolo:** Wayland: with DISPLAY set, Orca rewrites the keymap through Xwayland (xkbcomp), GNOME Shell can freeze

**Testo:**

> Orca 50.2, GNOME Shell 50.5 on Wayland (Debian testing). When DISPLAY is set in Orca's environment (the systemd user unit inherits it from the session), every time Orca sets up its modifier keys it reads the keyboard map through Xwayland with xkbcomp and writes it back. GNOME Shell then reloads its key bindings; at login this sometimes left GNOME Shell stuck (main thread waiting on a futex right after the reload, no extensions, the accessibility bus and notifications not answering), about one boot in six in our automatic tests.
>
> Under Wayland this is not needed, since Mutter holds back the Orca modifiers itself (meta-a11y-manager). Starting Orca without DISPLAY (`UnsetEnvironment=DISPLAY` in a drop-in for orca.service) avoided the freeze in all our later runs, and Orca started in 2 seconds instead of 19.
>
> Suggestion: skip the xkbcomp path when running under Wayland (XDG_SESSION_TYPE=wayland or WAYLAND_DISPLAY set).

## 4. Orca: il watchdog di 6 secondi

**Titolo:** orca.service WatchdogSec=6 kills Orca on slow machines and with slow speech synthesizers

**Testo:**

> Orca 50.2. The systemd user unit has WatchdogSec=6, and the default start timeout of 90 seconds. On a slow machine (a virtual machine without hardware acceleration) Orca needed more than 90 seconds to become ready and was killed and restarted three times, leaving the user without speech for about six minutes. With a neural speech module in Speech Dispatcher, the main loop sometimes waited more than 6 seconds in `speak()`, and the watchdog killed Orca again.
>
> For a screen reader, a slow start or a slow answer is better than being killed. Would a longer WatchdogSec (we use 30 seconds) and TimeoutStartSec (we use 5 minutes) be acceptable upstream?

## 5. Debian: live-build e l'installer su forky

Da inviare a `submit@bugs.debian.org`, dopo aver controllato <https://bugs.debian.org/live-build>:

```text
Package: live-build
Version: 1:20250814
Severity: normal

Building an image for testing (forky) with the Debian Installer included
(--debian-installer live --debian-installer-distribution git) fails with
live-build 1:20250814: the installer step asks for libfuse2, which cannot
be installed in forky.

The same configuration builds with live-build from git at commit 531cdb98
(2026-09-13), so it seems already fixed there: could a new upload bring
the fix to testing?

Configuration: lb config --distribution forky --debian-installer live
--debian-installer-distribution git --debian-installer-gui true
--archive-areas "main non-free-firmware" (full configuration:
https://github.com/Vabax-dev/VabaxOS/tree/main/image).
```

## 6. speech-dispatcher: la voce si ferma per sempre (filo degli eventi mai svegliato)

Causa del silenzio di speech-dispatcher nelle prove (2026-09-27): riprodotto nella macchina virtuale con solo eSpeak NG e in un sistema Debian forky minimo con `tests/upstream/speechd-reply-race.py`; con la correzione qui sotto 200 giri della prova e 2000 messaggi senza nessun blocco.

**Titolo:** Server audio: speech stops for good when a command with a reply arrives while a module sends audio (event thread never woken)

**Testo:**

> speech-dispatcher 0.12.1 (Debian 0.12.1-5), also current master. With server-side audio, speech sometimes stops for good until speech-dispatcher is restarted: messages are queued, `output_stop()` sends STOP again and again, nothing is spoken. We hit it about once in two automatic test runs with Orca 50 and the espeak-ng module.
>
> Stacks when it happens: the module (sd_espeak-ng) is blocked in `write()` of a 705 audio message in `module_tts_output_send_server()`, its stdout pipe full; the server's output thread waits in `output_read_event()` (output.c:359, `pthread_cond_wait(&output->event_cond, ...)`), while `speaking_module` shows `reading_message = 0, event = NULL, reading_events = 1`: nobody reads the module any more. Just before, the log has `200 OK VOICE LIST SENT`: Orca asked for the voices while the module was speaking.
>
> Cause: in `output_read_reply()`, after reading, the reply reader sets `reading_message = FALSE` and signals `reply_cond`. The event thread waits on `event_cond` for `reading_message` to drop, so if the reply reader got its reply, the event thread is never woken. `output_read_event()` does the symmetric thing correctly (it signals `reply_cond`, where reply readers wait).
>
> Reproducer: https://github.com/Vabax-dev/VabaxOS/blob/main/tests/upstream/speechd-reply-race.py (a long message, then LIST VOICES from a second connection, then a probe message that must end): stuck at round 1 or 2 without the fix, no stall in 200 rounds with it.
>
> Fix:
>
> ```diff
> --- a/src/server/output.c
> +++ b/src/server/output.c
> @@ -315,7 +315,8 @@
>  			message = output_read_message(output);
>  			pthread_mutex_lock(&output->read_mutex);
>  			output->reading_message = FALSE;
> -			pthread_cond_signal(&output->reply_cond);
> +			/* The event thread may be waiting for us to stop reading */
> +			pthread_cond_signal(&output->event_cond);
>  			if (!message)
>  				/* Module broke */
>  				break;
> ```

## 7. GJS: GNOME Shell si blocca all'avvio (toggle queue e GSettings)

Causa del blocco di GNOME Shell all'avvio (circa 2 avvii su 10): riprodotto in 20 secondi in un sistema Debian forky minimo con `tests/upstream/gjs-gsettings-deadlock.js`, con le stesse pile di GNOME Shell.

**Titolo:** Deadlock between the toggle queue lock and the GSettings backend lock (GC sweep vs dconf worker)

**Testo:**

> GJS 1.88.1 (Debian 1.89.2+really1.88.1-1), GLib 2.90.0, dconf 51.0; the code involved is the same in master. GNOME Shell 50.5 froze at login in about 2 boots out of 10 in our automatic tests.
>
> Main thread: GC → `ObjectInstance::update_heap_wrapper_weak_pointers()` takes the toggle queue lock for the whole sweep → `disassociate_js_gobject()` → `release_native_object()` → `g_object_remove_toggle_ref()` → last unref of a GSettings → weak notify `g_settings_backend_watch_weak_notify()` → waits for `backend->priv->lock`.
>
> "dconf worker" thread: a change written by another process → `g_settings_backend_dispatch_signal()` holds `backend->priv->lock` while it calls `g_weak_ref_get()` on every watched GSettings → a JavaScript-owned one goes from 1 to 2 references → `wrapped_gobj_toggle_notify()` → `ToggleQueue::lock()` spins for ever (a whole CPU).
>
> It is a variant of #558 (fixed by !895 for the weak_locations lock): here any code that runs while a GObject is finalized under the toggle queue lock can deadlock with another thread that toggles up while holding that code's lock.
>
> Reproducer (20 lines): https://github.com/Vabax-dev/VabaxOS/blob/main/tests/upstream/gjs-gsettings-deadlock.js — GSettings objects with a signal handler created and dropped with a GC after each batch, while another process changes a watched key; it deadlocks within seconds, with the same two stacks.
>
> A possible direction: collect the objects to release during the sweep and release them (the final unref) after the toggle queue lock is dropped, so that no finalization code runs under it.

## Stato

- 1, 2, 3, 4, 5: testi pronti, non ancora inviati (2026-09-26). Quando una segnalazione è inviata, scrivere qui il suo indirizzo.
- 6, 7: testi pronti (2026-09-27), non ancora inviati.
- ArcMenu (il separatore senza nome): non serve più, ArcMenu è stato tolto da VabaxOS (ADR-0025).
