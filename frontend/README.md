# React Build Output

Place the compiled React application in this directory so `backend/app.py` can
serve it alongside the Flask API. The preparation script will check for
`index.html` after you run your build.

Typical workflow:

```bash
# inside your React project
npm install
npm run build

# copy the build output into this repository
cp -r build/* /path/to/BIMProjMgmt/frontend/
```

If you output the build to another directory, set the `FRONTEND_DIR`
environment variable before launching the Flask server.
