/* ============================================================
   VUES AVANCÉES - SalleSense
   ============================================================ */

USE Prog3A25_bdSalleSense;
GO

-- Nettoyage des nouvelles vues si elles existent
IF OBJECT_ID('v_score_fiabilite_utilisateur', 'V') IS NOT NULL DROP VIEW v_score_fiabilite_utilisateur;
IF OBJECT_ID('v_chaine_evenements', 'V') IS NOT NULL DROP VIEW v_chaine_evenements;
IF OBJECT_ID('v_occurence_reservations', 'V') IS NOT NULL DROP VIEW v_occurence_reservations;
GO

/* ============================================================
   1) v_score_fiabilite_utilisateur
   ----------------------------------------------------------
   Pour chaque utilisateur, calcule:
   - Combien de réservations il a faites
   - Combien d'incidents de bruit il a causés
   - Un score simple de fiabilité
   ============================================================ */
CREATE VIEW v_score_fiabilite_utilisateur AS
SELECT
    u.idUtilisateur_PK,
    u.pseudo,
    u.courriel,
    -- Nombre de réservations
    COUNT(DISTINCT r.idReservation_PK) AS nb_reservations,
    -- Nombre d'incidents de bruit (>= 80 dB pendant leurs réservations)
    COUNT(DISTINCT CASE
        WHEN d.mesure >= 80 THEN d.idDonnee_PK
        ELSE NULL
    END) AS nb_incidents_bruit,
    -- Score simple: 100 - (incidents * 10)
    100 - (COUNT(DISTINCT CASE
        WHEN d.mesure >= 80 THEN d.idDonnee_PK
        ELSE NULL
    END) * 10) AS score_fiabilite
FROM Utilisateur u
LEFT JOIN Reservation r ON r.noPersonne = u.idUtilisateur_PK
LEFT JOIN Donnees d
    ON d.noSalle = r.noSalle
    AND d.dateHeure BETWEEN r.heureDebut AND r.heureFin
LEFT JOIN Capteur c ON c.idCapteur_PK = d.idCapteur AND c.type = 'BRUIT'
GROUP BY u.idUtilisateur_PK, u.pseudo, u.courriel;
GO

/* ======= EXEMPLES D'UTILISATION =======
-- Voir tous les utilisateurs avec leur score
SELECT * FROM v_score_fiabilite_utilisateur ORDER BY score_fiabilite DESC;

-- Utilisateurs problématiques (score < 70)
SELECT pseudo, nb_reservations, nb_incidents_bruit, score_fiabilite
FROM v_score_fiabilite_utilisateur
WHERE score_fiabilite < 70;
=========================================*/


/* ============================================================
   2) v_chaine_evenements
   ----------------------------------------------------------
   Montre chaque événement avec l'événement qui suit juste après
   dans la même salle (séquence d'événements)
   ============================================================ */
CREATE VIEW v_chaine_evenements AS
SELECT
    e1.idEvenement_PK,
    s.numero AS salle,
    e1.type AS evenement_actuel,
    d1.dateHeure AS moment_actuel,
    -- Événement suivant
    e2.type AS evenement_suivant,
    d2.dateHeure AS moment_suivant,
    -- Délai en minutes entre les deux événements
    DATEDIFF(MINUTE, d1.dateHeure, d2.dateHeure) AS delai_minutes
FROM Evenement e1
JOIN Donnees d1 ON d1.idDonnee_PK = e1.idDonnee
JOIN Salle s ON s.idSalle_PK = d1.noSalle
-- Joindre avec l'événement suivant dans la même salle
LEFT JOIN Donnees d2
    ON d2.noSalle = d1.noSalle
    AND d2.dateHeure = (
        SELECT MIN(d3.dateHeure)
        FROM Donnees d3
        WHERE d3.noSalle = d1.noSalle
        AND d3.dateHeure > d1.dateHeure
    )
LEFT JOIN Evenement e2 ON e2.idDonnee = d2.idDonnee_PK;
GO

/* ======= EXEMPLES D'UTILISATION =======
-- Voir toutes les séquences
SELECT * FROM v_chaine_evenements ORDER BY moment_actuel DESC;

-- Séquences ENTREE → BRUIT_FORT
SELECT salle, evenement_actuel, evenement_suivant, delai_minutes
FROM v_chaine_evenements
WHERE evenement_actuel = 'ENTREE' AND evenement_suivant = 'BRUIT_FORT';

-- Événements sans suite (dernier événement de la salle)
SELECT * FROM v_chaine_evenements WHERE evenement_suivant IS NULL;
=========================================*/


/* ============================================================
   3) v_occurence_reservations
   ----------------------------------------------------------
   Trouve quels utilisateurs réservent souvent les mêmes salles
   ============================================================ */
CREATE VIEW v_occurence_reservations AS
SELECT
    u1.idUtilisateur_PK AS utilisateur_1,
    u1.pseudo AS pseudo_1,
    u2.idUtilisateur_PK AS utilisateur_2,
    u2.pseudo AS pseudo_2,
    s.numero AS salle_commune,
    -- Combien de fois chacun a réservé cette salle
    COUNT(DISTINCT r1.idReservation_PK) AS nb_reservations_user1,
    COUNT(DISTINCT r2.idReservation_PK) AS nb_reservations_user2
FROM Reservation r1
JOIN Reservation r2 ON r1.noSalle = r2.noSalle
JOIN Utilisateur u1 ON u1.idUtilisateur_PK = r1.noPersonne
JOIN Utilisateur u2 ON u2.idUtilisateur_PK = r2.noPersonne
JOIN Salle s ON s.idSalle_PK = r1.noSalle
WHERE u1.idUtilisateur_PK < u2.idUtilisateur_PK  -- Éviter les doublons
GROUP BY u1.idUtilisateur_PK, u1.pseudo, u2.idUtilisateur_PK, u2.pseudo, s.numero;
GO

/* ======= EXEMPLES D'UTILISATION =======
-- Voir toutes les paires d'utilisateurs qui partagent des salles
SELECT * FROM v_matrice_cooccurrence;

-- Paires qui utilisent beaucoup la même salle
SELECT pseudo_1, pseudo_2, salle_commune,
       nb_reservations_user1, nb_reservations_user2
FROM v_matrice_cooccurrence
WHERE nb_reservations_user1 >= 2 AND nb_reservations_user2 >= 2;

-- Trouver avec qui 'alice' partage des salles
SELECT pseudo_2 AS collegue, salle_commune, nb_reservations_user2
FROM v_matrice_cooccurrence
WHERE pseudo_1 = 'alice'
ORDER BY nb_reservations_user2 DESC;
=========================================*/
