<?php
session_start();
session_unset();
session_destroy();
header("Location: https://blancostudio.dev/Login/login.html");
exit();
?>
