<?php
// Database connection
$servername = "localhost";
$username = "root";
$password = "";
$dbname = "booking_db";

$conn = new mysqli($servername, $username, $password, $dbname);

// Check connection
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

// Handle form submission
if ($_SERVER["REQUEST_METHOD"] == "POST") {
    $Nome = $conn->real_escape_string($_POST["first_name"]);
    $Cognome = $conn->real_escape_string($_POST["last_name"]);
    $email = $conn->real_escape_string($_POST["email"]);
    $phone = $conn->real_escape_string($_POST["phone"]);
    $service = $conn->real_escape_string($_POST["service"]);
    $data = $conn->real_escape_string($_POST["date"]);
    $time = $conn->real_escape_string($_POST["time"]);
    $note = $conn->real_escape_string($_POST["notes"]);

    $sql = "INSERT INTO parrucco (Nome, Cognome, email, phone, service, data, time, note) 
            VALUES ('$Nome', '$Cognome', '$email', '$phone', '$service', '$data', '$time', '$note')";

    if ($conn->query($sql) === TRUE) {
        header("Location: success.html");
        exit();
    } else {
        header("Location: error.html");
        exit();
    }

}

$conn->close();
?>
