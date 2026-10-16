# Payflows Watchdog (Team 11)

Agent Claude qui lit Payflows via MCP et relance dans Slack la bonne personne, au bon moment, avec le lien pour agir.

## Règles
- **En live** (boucle d'une minute, voir [LOOP_PROMPT.md](LOOP_PROMPT.md)) : facture soumise sans purchase order → PO pré-remplie en brouillon + alerte au demandeur avec le bouton « Vérifier et soumettre ta PO ».
- **En messages préparés** (postés une fois, voir `demo_messages.json` et `alerts_demo.json`) : morning brief DAF, validation en retard avec escalade, doublon marqué payé deux fois, circuit de validation jamais activé, reconduction tacite de contrat, pistes d'amélioration du circuit.

Le contexte complet, les décisions et le backlog sont dans le [README racine](../README.md).

## Brancher l'app Slack (5 min)
1. https://api.slack.com/apps : **Create New App**, puis **From an app manifest**. Choisir l'espace, coller `slack_app_manifest.yml` et créer l'app.
2. **Incoming Webhooks** : activer, puis **Add New Webhook to Workspace**. Choisir le canal et autoriser.
3. Copier l'URL du webhook dans `watchdog/.env` :
   `SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...`
   Cette URL est un secret : ne la colle jamais dans le chat ni sur Slack.
4. Tester avec `python3 post_alerts.py alerts_demo.json --only 0`.

## Démo en direct
1. Déposer `invoices/KES-2026-0312.pdf` dans Payflows (formulaire « Invoice without PO required ») : facture Kestrel Events de 6 900 € HT, sans PO.
2. Lancer le scan : Claude lit les factures soumises via MCP, détecte la nouvelle facture sans PO et écrit l'alerte.
3. Le message « Payflows Watchdog » arrive dans Slack avec le bouton « Créer ta purchase order ».

Le bac à sable est partagé entre toutes les équipes : annuler la facture de démo après le passage.
