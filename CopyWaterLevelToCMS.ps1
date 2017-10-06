param([string]$date, [string]$time, [string]$start_date, [string]$start_time, [string]$path, [string]$out, [string]$name, [string]$forceInsert)

if(!$date) {
	$date = (Get-Date).ToString('yyyy-MM-dd')
}

echo "CopyWaterLevelToCMS:: forecast date : $date $time $start_date $start_time $path $out $name"

python EXTRACTFLO2DWATERLEVEL.py -d $date `
    $(If ($time) {"-t $time"} Else {""}) `
    $(If ($start_date) {"-S $start_date"} Else {""}) `
    $(If ($start_time) {"-T $start_time"} Else {""}) `
    $(If ($path) {"-p $path"} Else {""}) `
    $(If ($out) {"-o $out"} Else {""}) `
    $(If ($name) {"-n $name"} Else {""}) `
    $(If ($forceInsert) {"-f $forceInsert"} Else {""})

$output_dir = If ($out) {".\OUTPUT\water_level-$out"} Else {".\OUTPUT\water_level-$date"}
pscp -i .\ssh\id_lahikos -r $output_dir uwcc-admin@10.138.0.6:/home/uwcc-admin/cfcwm/data/FLO2D/WL

if(Test-Path $output_dir){
    Compress-Archive -Force -Path $output_dir -DestinationPath "$output_dir.zip"
    pscp -i .\ssh\id_lahikos "$output_dir.zip" uwcc-admin@10.138.0.6:/home/uwcc-admin/cfcwm/data/FLO2D/WL
}