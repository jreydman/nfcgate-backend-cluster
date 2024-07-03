#!/bin/bash

vars=$(compgen -A variable)
subst=$(printf '${%s} ' $vars)
nginx_path="/etc/nginx"

find ${nginx_path}/ -type f \( -name "*.template.nginx" -o -name "*.template.conf" \) | while read template; do
    conf_file=$(echo $template | sed -E 's/\.template\.(nginx|conf)$/.conf/')
    envsubst "$subst" < $template > $conf_file
done

nginx -t
echo "Starting Nginx..."
nginx