param([string]$d, [string]$p, [string]$o, [string]$S, [string]$T)

if(!$d) {
	$d = (Get-Date).ToString('yyyy-MM-dd')
}

echo "CopyWaterLevelToCMS:: forecast date : $d $p $o $S $T"

python FLO2DTOWATERLEVEL.py -d $d `
    $(If ($p) {"-p $p"} Else {""}) `
    $(If ($o) {"-o $o"} Else {""}) `
    $(If ($S) {"-S $S"} Else {""}) `
    $(If ($T) {"-T $T"} Else {""})

$output_dir = If ($o) {".\OUTPUT\water_level-$o"} Else {".\OUTPUT\water_level-$d"}
C:\udp\pscp.exe -i .\ssh\id_lahikos -r $output_dir uwcc-admin@10.138.0.6:/home/uwcc-admin/cfcwm/data/FLO2D/WL