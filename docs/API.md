# API information

### For all api endpoints and their specific documentation, please refer to the Swagger documentation

## Swagger Documentation
Available at `<url>/api/docs` with `APP_SWAGGER_ENABLED=true` set as environment variable when using a local development server.

## General API structure (backend)
For the complete, detailed relationships between entities: please refer to the ER diagram.

The entire API backend is stateless and RESTful. This means that multiple instances of the backend can be run at the same time, and they will all function correctly.
However, the websocket server (everything inside `src.socketio`) is not stateless and should be run as a single instance. Running multiple instances will result in undefined behaviour.

Each entity has a Model, a Schema and a Resource class. The Model lies in the `model` package, in a file with the same name as the entity.
The model is the Mapper for SQLAlchemy and has all column definitions and relationships between other SQLAlchemy models.

A Schema lies in the `resource` package, in a file with the same name as the entity. The class name (of the schema) is the entity name appended with `Schema`.
The Schema defines and parses the JSON representation of the entity. It should function as a JSON to Entity Mapper and reverse.
The Schema is used to validate input JSON bodies, format output objects and documentation.

A Resource lies in the `resource` package, preferably in the same file as the Schema.
The resource functions as a RESTful API endpoint that accepts HTTP requests. As per RESTful spec, it has at most 4 methods for each CRUD operation on
an entity. Each function has `@swagger` decorators with information about what schema is returned / used in what use case / error message.
- `post()` - HTTP `POST` for create
- `get()` - HTTP `GET` for read
- `put()` - HTTP `PUT` for update
- `delete()` - HTTP `DELETE` for removal

Please note that not all endpoints support all CRUD operations, please refer to the Swagger documentation for more information.

A Resource parses the query methods and/or JSON body and manipulates / retrieves the SQLAlchemy Models accordingly.
It functions as both the Controller and the View for an entity.

Endpoints of objects that allow listing of all objects are usually suffixed with `/list` (e.g. `/api/spell/list`).

#### Conventions on API responses
All API responses are JSON objects. Except the `DELETE` method, all HTTP 200 responses will return the object itself rather than a status and/or message field.
All non-200 responses will have a `status` key with the value `error` and a `message` key with a human-readable error message.
Please note that the `auth` endpoints don't follow these conventions, as they are not part of the RESTful API. 

For more details, please consult the Swagger documentation.

- `GET` - Unless specified otherwise, requires always an `id` parameter in the **query string**. If the id is not found, it will return a 404. It will always return the object schema on HTTP 200. No status key is then returned.
- `POST` - Requires a JSON body with the object schema. **No id** (Primary Key of the entity) has to be present in the request body (it is ignored anyway). **ALL** other fields are **mandatory** (unless specified otherwise). It will automatically be assigned and returned in the response body. It will return the object schema on HTTP 200. It will return a 400 if the object is not valid.
- `PUT` - Requires a JSON body with the object schema. An **id (PK) has to be present** in the **request body**. All other fields are *optional*. Please note that not all fields are updatable. Please refer to the Swagger & PyDoc documentation for more info. A JSON object (schema) is returned on HTTP 200. It will return a 400 if the object is not valid. It will return a 404 if the object is not found.
- `DELETE` - Requires an `id` parameter in the **query string**. It will return a HTTP 200 with `status` key `success` if the object is deleted. It will return a 404 if the object is not found.

Unless clearly specified otherwise, the `type` field is always IGNORED in the request body. The `type` field is used for polymorphic identities. For POST request, this type is determined by the used endpoint and is therefore also never required.
When applicable, the `type` field is present in the response body and can be safely used to determine the polymophic identity (so which fields are present in the response body), depending on the properties the polymorphic object has.
Eg. a mine has a `mined_amount` field that is only present in the `Mine` object. The `type` field can be used to determine if the object is a `Mine` or not. For a complete overview of polymorphic object and their fields, please refer to the ER-diagram.

#### A special note on registering new endpoints
Each RESTful endpoint (=Resource) should be registered with an `attach_resource()` function defined in the 
resource file. This method should be mostly copied over from other examples, and be modified accordingly. 
Finally, add this function to the `resource.__init__#attach_resources()` by importing it locally and invoking it.

The reason this is done this way is because the current flask-restful-swagger-3 package does not support multiple Flask route
blueprints. So they all have to be bundled to one. The package is the only that adds Swagger 3 support, but is unfortunately unmaintained and broken in many ways.


#### A special note on creating new buildings, entities and tasks that belong to an island
When creating a new entity or building that belongs to an island (and all implementing classes), the accompanying `Schema` should also be 
registered in the `resource/island.py` file. For new task subclasses, these schema's should be registered in the `resource/placeable.py` class. Entity schema's should be added to the `_resolve_placeable_schema_for_type()` method and buildings
in the `_resolve_building_schema_for_type()` method. Tasks in the `_resolve_task_schema_for_type()` method in `placeable.py`. This is necessary for the `island` class to parse the entities and buildings to JSON values to pass
on to the frontend.

#### A special note on grouped objects
Grouped objects such as `placeble` and `entity` have all a common `DELETE` endpoint (`/api/placeable` for placeables, `/api/entity` for entities). This endpoint will delete all objects that are related to the object that is being deleted. No specification of the subclass / type of object is needed.

## Access constraints
All non-GET endpoints (POST, PUT, DELETE) must be invoked by either an admin or the user that owns the object (= the user/player that has said object associated with himself or the island it owns). Failure will result in a 403 error.
GET endpoints are not subject to this constraint because they are read-only and do not modify the database.

Disabling this constraint can be done by setting the `CHECK_DATA_OWNERSHIP` environment variable to `false`. This will however still log a warning to the server console.

## Data constraints
The following variables have certain constraints on their values. It is safe to assume these names are unique across the application (therefore these constraints are applicable accorss all variables with said name).
- `level`: `value` >= 0 (entities & buildings)
- `xpos`: `value` >= -7 and `value` <= 7 (grid size)
- `zpos`: `value` >= -7 and `value` <= 7 (grid size)
- `rotation`: `value` >= 0 and `value` <= 3 (north, east, south, west)
- `cost`: `value` >= 0 (blueprints)
- `buildtime`: `value` >= 0 (blueprints)
- `used_crystals`: `value` >= 0 (tasks)
- `to_level`: `value` >= 0 (tasks)
- `multiplier`: `value` >= 0 (gem attributes)
- `mined_amount`: `value` >= 0 (mines)
- `crystals`: `value` >= 0 (player)
- `xp`: `value` >= 0 (player)
- `mana`: `value` >= 0 and `value` <= 1000 (player)
- `audio_volume`: `value` >= 0 and `value` <= 100 (user settings)
- `performance`: `value` >= 0 and `value` <= 3 (user settings)
- `selected_currency`: `value` >= 0 and `value` <= 2 (user settings)
- `horz_sensivity`: `value` >= 0 and `value` <= 100 (user settings)
- `vert_sensivity`: `value` >= 0 and `value` <= 100 (user settings)