# energie-hdf-france

# How to run

Setup database with init_db.sql then run :

```
docker build -t energy-pipeline .  
docker run --rm --env-file .env --network=host energy-pipeline 
```

.env structure can be found in .env.exemple