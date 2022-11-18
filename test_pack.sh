#!/bin/sh

zip -q -r amiyabot-arknights-hsyhhssyy-furniture-1.0.zip *
rm -rf ../../amiya-bot-v6/plugins/amiyabot-arknights-hsyhhssyy-furniture-1_0
mv amiyabot-arknights-hsyhhssyy-furniture-1.0.zip ../../amiya-bot-v6/plugins/
docker restart amiya-bot 