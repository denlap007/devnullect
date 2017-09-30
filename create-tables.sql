CREATE TABLE group
(
  group_id INT NOT NULL,
  group_name VARCHAR(32),
  PRIMARY KEY (group_id)
);

CREATE TABLE user
(
  user_id INT NOT NULL,
  username VARCHAR(32),
  group_id INT NOT NULL,
  PRIMARY KEY (user_id),
  FOREIGN KEY (group_id) REFERENCES group(group_id)
);

CREATE TABLE resource
(
  resource_id INT NOT NULL,
  timestamp DATE NOT NULL,
  resource VARCHAR(500) NOT NULL,
  PRIMARY KEY (resource_id)
);

CREATE TABLE handles
(
  isHandled TINYINT(1) NOT NULL,
  user_id INT NOT NULL,
  resource_id INT NOT NULL,
  PRIMARY KEY (user_id, resource_id),
  FOREIGN KEY (user_id) REFERENCES user(user_id),
  FOREIGN KEY (resource_id) REFERENCES resource(resource_id)
);
