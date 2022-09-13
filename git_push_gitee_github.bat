rem git config --global user.email "accountbelongstox@163.com"
rem git config --global user.name "accountbelongstox"

git branch -M 'master'
git add .
git commit -m "new amend"
ssh -T git@gitee.com
git push -u gitee master

git branch -M 'main'
git add .
git commit -m "new amend"
ssh -T git@github.com
git push -u github main

git push -u gitee-public "master"