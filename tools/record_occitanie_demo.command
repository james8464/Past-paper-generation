#!/bin/zsh
set -euo pipefail

project_root="${0:A:h:h}"
recording_dir="$project_root/output/occitanie-2026/video"
recording_path="$recording_dir/Paper-Creator-NSI-Occitanie-demo.mov"

locked=$(/usr/sbin/ioreg -n Root -d1 2>/dev/null | /usr/bin/grep -c 'CGSSessionScreenIsLocked.*Yes' || true)
if [[ "$locked" != "0" ]]; then
  /usr/bin/osascript -e 'display alert "Déverrouillez le Mac" message "La démonstration doit montrer la vraie application. Déverrouillez la session, puis relancez ce fichier." as critical'
  exit 1
fi

/bin/mkdir -p "$recording_dir"

cd "$project_root/macOS"
make build-and-run-background

/usr/bin/osascript -e 'display dialog "Paper Creator est prêt. Fermez les fenêtres personnelles, placez l’application comme indiqué dans le scénario, puis cliquez sur Démarrer. macOS vous demandera de sélectionner la zone à enregistrer." buttons {"Annuler", "Démarrer"} default button "Démarrer" cancel button "Annuler" with title "Démonstration Prix Occitanie"'

/usr/sbin/screencapture -i -J video -g -k "$recording_path"

if [[ -s "$recording_path" ]]; then
  /usr/bin/open -R "$recording_path"
  /usr/bin/osascript -e 'display dialog "La vidéo a été enregistrée. Regardez-la en entier et vérifiez qu’aucune donnée personnelle, erreur ou affirmation non prouvée n’apparaît avant de la partager." buttons {"OK"} default button "OK" with title "Enregistrement terminé"'
else
  /usr/bin/osascript -e 'display alert "Aucune vidéo enregistrée" message "L’enregistrement a été annulé ou macOS n’a pas accordé l’autorisation de capturer l’écran." as warning'
  exit 1
fi

