# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **SalleSense** project combining:
- **Raspberry Pi GPIO control** (Python) for hardware sensors/LED control
- **SQL Server database** for room reservation and sensor monitoring system

The project manages room reservations with IoT sensor integration (movement, noise, camera) and includes user management with blacklist functionality.

## Database Setup Commands

All SQL scripts are in the [Script_bd/](Script_bd/) directory and must be run in this order:

```bash
# 1. Create database
sqlcmd -i Script_bd/ceration_bd.sql

# 2. Create tables
sqlcmd -i Script_bd/creationTables.sql

# 3. Add constraints and foreign keys
sqlcmd -i Script_bd/contrainteSql.sql

# 4. Insert test data
sqlcmd -i Script_bd/InsertionSql.sql

# 5. Create stored procedures for authentication
sqlcmd -i Script_bd/ProcedureStocke.sql

# 6. Create triggers (reservation overlap, blacklist enforcement)
sqlcmd -i Script_bd/Trigger.sql

# 7. Optional: Advanced procedures, views, and constraints
sqlcmd -i Script_bd/ProceduresAvancees.sql
sqlcmd -i Script_bd/View.sql
sqlcmd -i Script_bd/ViewsComplexes.sql
sqlcmd -i Script_bd/checkConstraintsAvancees.sql
sqlcmd -i Script_bd/contraintesAvancees.sql
```

**Database name**: `Prog3A25_bdSalleSense`

## Python Hardware Scripts

Running on Raspberry Pi with GPIO hardware control. **Note**: These require physical Raspberry Pi hardware and `RPi.GPIO` library.

- [labo.py](labo.py) - Interactive LED control via user input (GPIO pins 17, 4, 27)
- [boutton.py](boutton.py) - Button state monitoring (GPIO pin 27 with pull-up)
- [proto-final.py](proto-final.py) - Button press counter controlling LEDs (state machine)

To run on Raspberry Pi:
```bash
sudo python3 labo.py       # For interactive LED control
sudo python3 boutton.py    # For button monitoring
sudo python3 proto-final.py # For complete button/LED system
```

## Database Architecture

### Core Tables
- **Utilisateur**: User accounts with hashed passwords (SHA2_256 with salt)
- **Blacklist**: Banned users (enforced by triggers)
- **Salle**: Rooms with capacity limits
- **Reservation**: Room bookings with overlap prevention
- **Capteur**: IoT sensors (MOUVEMENT, BRUIT, CAMERA)
- **Donnees**: Sensor readings (numeric measures or photo paths)
- **Evenement**: Events triggered by sensor data

### Key Business Rules (Enforced by DB)
- Users cannot reserve if blacklisted (trg_check_blacklist)
- No overlapping reservations per room (trg_pasDeChevauchement)
- Email validation with format checks
- Reservation times must be valid (start < end, positive person count)
- Password security via stored procedures (usp_Utilisateur_Create, usp_Utilisateur_Login)

### Authentication Flow
Use stored procedures for secure password handling:
```sql
-- Create user
EXEC dbo.usp_Utilisateur_Create
  @Pseudo='username',
  @Courriel='user@example.com',
  @MotDePasse='password',
  @UserId OUTPUT;

-- Login
EXEC dbo.usp_Utilisateur_Login
  @Courriel='user@example.com',
  @MotDePasse='password',
  @UserId OUTPUT;
-- Returns user ID if successful, -1 if failed
```

## Important Notes

- SQL scripts use T-SQL syntax (SQL Server) with `GO` batch separators
- Python scripts require `sudo` for GPIO access on Raspberry Pi
- GPIO pins configured: 17 (green LED), 4 (red LED), 27 (button/input)
- The database enforces referential integrity - delete in reverse dependency order
