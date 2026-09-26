# Segnalazioni ai progetti esterni

Decisione di Vabax (2026-09-26, risposta 13B): le segnalazioni dei difetti trovati le prepara Claude. GNOME Shell e Orca usano GitLab di GNOME, Debian usa la posta: servono account che la sessione di sviluppo non ha. Qui ci sono i testi pronti, in inglese, da incollare.

Dove si incollano:

- GNOME Shell: <https://gitlab.gnome.org/GNOME/gnome-shell/-/issues/new> (serve un account di GitLab di GNOME);
- Orca: <https://gitlab.gnome.org/GNOME/orca/-/issues/new> (stesso account);
- Debian: un messaggio di posta a `submit@bugs.debian.org`, con le prime righe esattamente come sono scritte qui sotto.

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

## Stato

- 1, 2, 3, 4, 5: testi pronti, non ancora inviati (2026-09-26). Quando una segnalazione è inviata, scrivere qui il suo indirizzo.
- ArcMenu (il separatore senza nome): non serve più, ArcMenu è stato tolto da VabaxOS (ADR-0025).
