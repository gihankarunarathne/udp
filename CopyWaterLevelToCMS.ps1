param([string]$d, [string]$p)

if(!$d) {
	$d = (Get-Date).ToString('yyyy-MM-dd')
}

echo "CopyWaterLevelToCMS:: forecast date : $d $p"

python FLO2DTOWATERLEVEL.py -d $d $(If ($p) {"-p $p"} Else {""})

C:\udp\pscp.exe -i .\ssh\id_lahikos -r  .\OUTPUT\water_level-$d uwcc-admin@10.138.0.6:/home/uwcc-admin/cfcwm/data/FLO2D/WL