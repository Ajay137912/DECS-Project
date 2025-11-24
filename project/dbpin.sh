while true; do 
    pgrep -u postgres | xargs -n 1 sudo taskset -cp 2 > /dev/null 2>&1
    echo "Setting to 2"
    sleep 1
    
done