# Stop the spinner processes (.weaver\hogs.py) and the stab experiment runners of this stream; leaves every other process alone.
Get-CimInstance Win32_Process | Where-Object { $_.Name -like 'python*' -and ($_.CommandLine -match 'hogs\.py' -or $_.CommandLine -match 'stab_hog_run\.py') } | ForEach-Object {
    "stop $($_.ProcessId) $($_.CommandLine.Substring(0, [Math]::Min(80, $_.CommandLine.Length)))"
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
}
