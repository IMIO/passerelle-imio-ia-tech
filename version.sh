version=`echo $(cat setup.py | grep "version =" | cut -d '"' -f 2 && echo "-" && date "+%Y%m%d%H%M%S" && echo "~" && git log --pretty=format:'%h' -n 1) | tr -d "[:space:]"`
echo $version
