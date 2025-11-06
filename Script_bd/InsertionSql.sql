-- ==========================================
--  Script d’insertion de données de test
-- ==========================================
USE Prog3A25_bdSalleSense;

-- ──────────────
-- Utilisateur
-- ──────────────
INSERT INTO Utilisateur (pseudo, courriel, motDePasse) VALUES
  ('alice', 'alice@example.com', 'pwdAlice'),
  ('bob',   'bob@example.com',   'pwdBob'),
  ('carol', 'carol@example.com', 'pwdCarol');

-- ──────────────
-- Blacklist
-- ──────────────
INSERT INTO Blacklist (idUtilisateur) VALUES
  (2);   -- Bob est banni (idUtilisateur=2)

-- ──────────────
-- Salle
-- ──────────────
INSERT INTO Salle (numero, capaciteMaximale) VALUES
  ('A-101', 20),
  ('B-202', 12),
  ('C-303', 30);

-- ──────────────
-- Reservation
-- ──────────────
INSERT INTO Reservation (heureDebut, heureFin, noSalle, noPersonne, nombrePersonne) VALUES
  ('2025-09-19 10:00:00', '2025-09-19 12:00:00', 1, 1, 4), -- Alice réserve A-101
  ('2025-09-19 13:30:00', '2025-09-19 15:00:00', 2, 3, 2), -- Carol réserve B-202
  ('2025-09-20 09:00:00', '2025-09-20 11:00:00', 3, 1, 10); -- Alice réserve C-303

-- ──────────────
-- Capteur
-- ──────────────
INSERT INTO Capteur (nom, type) VALUES
  ('PIR-1', 'MOUVEMENT'),
  ('MIC-1', 'BRUIT'),
  ('CAM-1', 'CAMERA');

-- ──────────────
-- Donnees
-- ──────────────
INSERT INTO Donnees (dateHeure, idCapteur, mesure, photo, noSalle) VALUES
  ('2025-09-18 08:05:00', 1, NULL, NULL, 1),                -- mouvement A-101
  ('2025-09-18 08:06:30', 2, 52.3, NULL, 1),                -- bruit A-101
  ('2025-09-18 08:07:10', 3, NULL, 'photos/a101_1.jpg', 1), -- photo A-101
  ('2025-09-18 09:15:00', 2, 72.8, NULL, 2),                -- bruit B-202
  ('2025-09-18 09:16:10', 1, NULL, NULL, 2);                -- mouvement B-202

-- ──────────────
-- Evenement
-- ──────────────
INSERT INTO Evenement (type, idDonnee, description) VALUES
  ('ENTREE',     1, 'Présence détectée en salle A-101'),
  ('BRUIT_FORT', 2, 'Niveau sonore élevé mesuré en salle A-101'),
  ('CAPTURE',    3, 'Photo enregistrée par caméra CAM-1'),
  ('BRUIT_FORT', 4, 'Pic sonore en salle B-202'),
  ('SORTIE',     5, 'Fin de détection de présence en salle B-202');
