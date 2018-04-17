# deploy

在 _config.yml 文件内设置deploy的值

```
deploy:
  type: git
  repo: git@github.com:yourname/yourname.github.io.git
  branch: master
```

然后在 hexo d 时，就会自动将public内的文件push到github

# theme

theme设置为next，然后在 themes/next/_config.yml 中设置主题相关

比如 Schemes 推荐设置为 Mist