# Set the file path
$jsonPath = "D:\Documents\PowerShell\RoosterKeep.json"

# Read entire file content
$jsonRaw = Get-Content -Path $jsonPath -Raw

# Extract BlockCodes
$blockCodesMatch = [regex]::Match($jsonRaw, '"BlockCodes"\s*:\s*{([^}]+)}')
$blockCodesRaw = $blockCodesMatch.Groups[1].Value

# Parse BlockCodes into a hashtable
$blockCodeMap = @{}
$blockCodesRaw -split ',"' | ForEach-Object {
    if ($_ -match '"?(\d+)"?\s*:\s*"([^"]+)"') {
        $blockCodeMap[$matches[1]] = $matches[2]
    }
}

# Extract BlockIds array (after "BlockIds": [ and before ])
$blockIdsMatch = [regex]::Match($jsonRaw, '"BlockIds"\s*:\s*\[([^\]]+)\]')
$blockIdsRaw = $blockIdsMatch.Groups[1].Value

# Turn the BlockIds into an array and clean up spacing
$blockIds = $blockIdsRaw -split ',' | ForEach-Object { $_.Trim() }

# Count how many times each ID appears
$blockCounts = $blockIds | Group-Object | Sort-Object Count -Descending

# Output results
foreach ($group in $blockCounts) {
    $id = $group.Name
    $count = $group.Count
    $blockName = if ($blockCodeMap.ContainsKey($id)) { $blockCodeMap[$id] } else { "UNKNOWN ID: $id" }
    Write-Host "There are $count blocks of $blockName in this schematic."
}
