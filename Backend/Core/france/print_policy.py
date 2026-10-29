# Versioned French notices describe review limits without granting approval.

V34_PRINT_POLICY = "fr-nsi-v34-internal-review-v1"
V35_PRINT_POLICY = "fr-nsi-v35-internal-review-v1"
V36_PRINT_POLICY = "fr-nsi-v36-model-review-v1"
INTERNAL_REVIEW_POLICIES = frozenset(
    {V34_PRINT_POLICY, V35_PRINT_POLICY, V36_PRINT_POLICY}
)
V34_REVIEW_NOTICE = "Entraînement non officiel. Difficulté et durée non calibrées."
V34_CREDIT_NOTICE = "Barème indicatif, sans validation enseignante."
V34_CORRECTION_GUIDANCE = (
    "Barème indicatif : attribuer uniquement les crédits explicitement justifiés. "
    "Accepter une méthode équivalente correcte. Ne pas compter deux fois le même "
    "élément. Ce corrigé reste sans validation enseignante ni calibration auprès "
    "d'élèves. Vérifier les réponses, variantes et cas limites avant une évaluation."
)
V34_FOOTER = "Keldin - entraînement non officiel - non calibré"
