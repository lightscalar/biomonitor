# Try to launch mongodb; do it in the background.
mongod &

# Launch the dev version of the website in the background.
npm run dev &

# Finally, launch the python webserver itself. Keep it in the foreground.
python server/server.py && fg
