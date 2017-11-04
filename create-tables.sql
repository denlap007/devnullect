CREATE TABLE `group`
(
  id BIGINT NOT NULL,
  PRIMARY KEY ( id )
);

CREATE TABLE `user`
(
  id BIGINT NOT NULL,
  PRIMARY KEY ( id )
);

CREATE TABLE resource
(
  id INT NOT NULL AUTO_INCREMENT,
  rs_content VARCHAR(2000) NOT NULL,
  rs_date DATETIME NOT NULL,
  PRIMARY KEY (id)
);

CREATE TABLE list
(
  id INT NOT NULL AUTO_INCREMENT,
  title VARCHAR(50) NOT NULL,
  user_id BIGINT NOT NULL,
  active BOOL DEFAULT 0,
  PRIMARY KEY (id),
  UNIQUE (title, user_id),
  FOREIGN KEY (user_id) REFERENCES `user`(id)
);


CREATE TABLE group_user
(
  id INT NOT NULL AUTO_INCREMENT,
  group_id BIGINT NOT NULL,
  user_id BIGINT NOT NULL,
  PRIMARY KEY (id),
  FOREIGN KEY (group_id) REFERENCES `group`(id),
  FOREIGN KEY (user_id) REFERENCES `user`(id)
);

CREATE TABLE resource_list
(
  id INT NOT NULL AUTO_INCREMENT,
  resource_id INT NOT NULL,
  list_id INT NOT NULL,
  PRIMARY KEY (id),
  FOREIGN KEY (resource_id) REFERENCES resource(id),
  FOREIGN KEY (list_id) REFERENCES list(id)
);
