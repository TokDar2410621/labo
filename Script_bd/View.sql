/* ------------------------------------------------------------
  1) Dernier occupant d’une salle
     → Dernière réservation par salle via MAX(heureDebut)
     Tables: Salle, Reservation, Utilisateur
-------------------------------------------------------------*/


USE Prog3A25_bdSalleSense;

IF OBJECT_ID('v_dernier_occupant_salle', 'U') IS NOT NULL DROP VIEW v_dernier_occupant_salle;
IF OBJECT_ID('v_bruit_max_personnes', 'U') IS NOT NULL DROP VIEW v_bruit_max_personnes;
IF OBJECT_ID('v_reservations_salle', 'U') IS NOT NULL DROP VIEW v_reservations_salle;
IF OBJECT_ID('v_salles_occupees_now', 'U') IS NOT NULL DROP VIEW v_salles_occupees_now;
GO
CREATE VIEW v_dernier_occupant_salle AS
SELECT
  s.idSalle_PK,
  s.numero AS salleNumero,
  r.idReservation_PK,
  r.heureDebut,
  r.heureFin,
  u.idUtilisateur_PK AS idOccupant,
  u.pseudo,
  u.courriel
FROM Salle s
LEFT JOIN Reservation r
  ON r.noSalle = s.idSalle_PK
 AND r.heureDebut = (
       SELECT MAX(r2.heureDebut)
       FROM Reservation r2
       WHERE r2.noSalle = s.idSalle_PK
     )
LEFT JOIN Utilisateur u
  ON u.idUtilisateur_PK = r.noPersonne;
GO


/* ======= EXEMPLES D’UTILISATION =======
-- Voir le dernier occupant de TOUTES les salles
SELECT * FROM v_dernier_occupant_salle;

-- Filtrer une salle par son id
SELECT * FROM v_dernier_occupant_salle WHERE idSalle_PK = 1;

-- Filtrer une salle par son numéro
SELECT * FROM v_dernier_occupant_salle WHERE salleNumero = 'A-101';

-- Voir seulement l’occupant (pseudo + email) de la salle 1
SELECT salleNumero, pseudo, courriel
FROM v_dernier_occupant_salle
WHERE idSalle_PK = 1;
=======================================*/


/* ------------------------------------------------------------
  2) Les 5 dernières réservations d’une salle
     → Vue simple; on limite à 5 dans la requête avec ORDER BY + LIMIT
     Tables: Reservation
-------------------------------------------------------------*/
CREATE VIEW v_reservations_salle AS
SELECT
  r.idReservation_PK,
  r.noSalle,
  r.noPersonne,
  r.heureDebut,
  r.heureFin,
  r.nombrePersonne
FROM Reservation r;
GO
/* ======= EXEMPLES D’UTILISATION =======
-- 5 dernières réservations de la salle 1
SELECT *
FROM v_reservations_salle
WHERE noSalle = 1
ORDER BY heureDebut DESC
LIMIT 5;

-- 5 dernières réservations de la salle 2, avec la durée en minutes
SELECT idReservation_PK, noSalle, noPersonne, heureDebut, heureFin,
       TIMESTAMPDIFF(MINUTE, heureDebut, heureFin) AS dureeMin
FROM v_reservations_salle
WHERE noSalle = 2
ORDER BY heureDebut DESC
LIMIT 5;

-- Pour une autre salle (ex. 7), même pattern :
-- SELECT * FROM v_reservations_salle WHERE noSalle = 7 ORDER BY heureDebut DESC LIMIT 5;
=======================================*/

/* ------------------------------------------------------------
  4) Personnes ayant atteint un seuil de bruit pendant leur réservation
     → Utilise Donnees(noSalle, dateHeure, mesure) + intervalle de Reservation
     → Seuil par défaut: 80 (ajuste dans le WHERE)
     Tables: Reservation, Utilisateur, Donnees
-------------------------------------------------------------*/
CREATE VIEW v_bruit_max_personnes AS
SELECT DISTINCT
  u.idUtilisateur_PK,
  u.pseudo,
  u.courriel,
  r.idReservation_PK,
  r.noSalle,
  r.heureDebut,
  r.heureFin,
  d.dateHeure   AS dateBruit,
  d.mesure      AS niveau
FROM Reservation r
JOIN Utilisateur u ON u.idUtilisateur_PK = r.noPersonne
JOIN Donnees d
  ON d.noSalle = r.noSalle
 AND d.dateHeure BETWEEN r.heureDebut AND r.heureFin

WHERE d.mesure >= 80;
GO
  -- ← ajuster le seuil ici (ex.: 75, 85, 90, etc.)
/*JOIN Evenement e ON e.idDonnee = d.idDonnee_PK AND e.type='BRUIT_FORT' peut etre mieux parce que l'on va definir l'evenement*/

/* ======= EXEMPLES D’UTILISATION =======
-- Voir toutes les personnes qui ont dépassé le seuil (par défaut 80)
SELECT * FROM v_bruit_max_personnes ORDER BY dateBruit DESC;

-- Filtrer par salle (ex. salle 2)
SELECT * FROM v_bruit_max_personnes
WHERE noSalle = 2
ORDER BY dateBruit DESC;

-- Filtrer par période (ex. événement de la semaine en cours)
SELECT *
FROM v_bruit_max_personnes
WHERE dateBruit >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
ORDER BY dateBruit DESC;

-- Voir seulement les infos des personnes (sans doublons)
SELECT DISTINCT idUtilisateur_PK, pseudo, courriel
FROM v_bruit_max_personnes;

-- CHANGER LE SEUIL :
--   Éditer la vue et modifier "WHERE d.mesure >= 80" par la valeur voulue,
--   puis la recréer avec CREATE OR REPLACE VIEW.
=======================================*/
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