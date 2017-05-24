param([string]$d)

if(!$d) {
	$d = (Get-Date).ToString('yyyy-MM-dd')
}

echo "forecast date : $d"

python FLO2DTOLEVEL.py $d

C:\udp\pscp.exe -i .\ssh\id_lahikos -r  .\OUTPUT\water_level-$d uwcc-admin@10.138.0.6:/home/uwcc-admin/cfcwm/data/FLO2D/WL