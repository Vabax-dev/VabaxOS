# VabaxOS (ADR-0027): "ripristino" opens the spoken menu of the system
# restore. In the recovery mode of the USB stick (no desktop, voice on),
# the console says so at login.
alias ripristino='sudo vabaxos-restore --console'
alias restore-system='sudo vabaxos-restore --console'
case " $(cat /proc/cmdline 2>/dev/null) " in
    *" boot=live "*"systemd.unit=multi-user.target"*)
        if [ -t 1 ] && [ -z "${VABAXOS_RESTORE_HINT:-}" ]; then
            export VABAXOS_RESTORE_HINT=1
            case "${LANG:-}" in
                it*) echo "Modalità di recupero. Per ripristinare il VabaxOS installato su questo computer scrivi ripristino e premi Invio." ;;
                *) echo "Recovery mode. To restore the VabaxOS installed on this computer, type restore-system and press Enter." ;;
            esac
        fi
        ;;
esac
