<?php
session_start();

// Configurazione sicura dei cookie di sessione
session_set_cookie_params([
    'secure' => true,
    'httponly' => true,
    'samesite' => 'Strict',
]);

// Verifica se l'utente è loggato e ha il ruolo di admin
if (!isset($_SESSION['logged_in']) || $_SESSION['logged_in'] !== true || $_SESSION['role'] !== 'admin') {
    header("Location: https://blancostudio.dev/Login/login.html");
    exit();
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bookings</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f3f4f6;
            color: #333;
            padding: 30px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        h1 {
            color: #333;
        }
        .logout {
            margin-top: 20px;
        }
        .logout a {
            text-decoration: none;
            color: white;
            background-color: #007bff;
            padding: 10px 15px;
            border-radius: 5px;
        }
        .logout a:hover {
            background-color: #0056b3;
        }
        .booking-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        .booking-table th, .booking-table td {
            padding: 12px;
            border: 1px solid #ddd;
            text-align: left;
        }
        .booking-table th {
            background-color: #000;
            color: white;
        }
        .booking-table td {
            background-color: white;
        }
        .booking-table tr:nth-child(even) {
            background-color: #f9f9f9;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>All Bookings</h1>

        <?php
        // Database connection
        $servername = "localhost";
        $username = "root";
        $password = "";
        $dbname = "booking_db";

        $conn = new mysqli($servername, $username, $password, $dbname);

        if ($conn->connect_error) {
            die("Connection failed: " . $conn->connect_error);
        }

        // Recupera tutte le prenotazioni dal database
        $sql = "SELECT * FROM parrucco";
        $result = $conn->query($sql);

        if ($result->num_rows > 0) {
            echo "<table class='booking-table'>
                    <tr>
                        <th>Nome</th>
                        <th>Cognome</th>
                        <th>Email</th>
                        <th>Phone</th>
                        <th>Service</th>
                        <th>Date</th>
                        <th>Time</th>
                        <th>Notes</th>
                    </tr>";

            while ($row = $result->fetch_assoc()) {
                echo "<tr>
                        <td>" . htmlspecialchars($row["Nome"]) . "</td>
                        <td>" . htmlspecialchars($row["Cognome"]) . "</td>
                        <td>" . htmlspecialchars($row["email"]) . "</td>
                        <td>" . htmlspecialchars($row["phone"]) . "</td>
                        <td>" . htmlspecialchars($row["service"]) . "</td>
                        <td>" . htmlspecialchars($row["data"]) . "</td>
                        <td>" . htmlspecialchars($row["time"]) . "</td>
                        <td>" . htmlspecialchars($row["note"]) . "</td>
                      </tr>";
            }

            echo "</table>";
        } else {
            echo "<p>No bookings found.</p>";
        }

        $conn->close();
        ?>

        <!-- Logout button -->
        <div class="logout">
            <a href="logout.php">Logout</a>
        </div>
    </div>
</body>
</html>
