<?php
$slug = preg_replace('/[^a-z0-9-_]/i', '', $_GET['id'] ?? '');
$mapFile = __DIR__ . '/mapping.csv';

if ($slug && file_exists($mapFile)) {
    if (($handle = fopen($mapFile, 'r')) !== false) {
        while (($row = fgetcsv($handle)) !== false) {
            if (strcasecmp(trim($row[0]), $slug) === 0 && !empty($row[1])) {
                fclose($handle);
                header("Location: https://docs.google.com/spreadsheets/d/" . trim($row[1]) . "/edit");
                exit;
            }
        }
        fclose($handle);
    }
}

http_response_code(404);
exit('Spreadsheet link not found.');
