CREATE TABLE `group`
(
  group_id INT NOT NULL AUTO_INCREMENT,
  PRIMARY KEY ( group_id )
)ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `user`
(
  user_id INT NOT NULL AUTO_INCREMENT,
  PRIMARY KEY ( user_id )
);

CREATE TABLE resource
(
  resource_id INT NOT NULL AUTO_INCREMENT,
  resource_content INT NOT NULL,
  PRIMARY KEY (resource_id)
);

CREATE TABLE toDoList
(
  toDoList_id INT NOT NULL AUTO_INCREMENT,
  toDoListName INT NOT NULL,
  user_id INT NOT NULL,
  PRIMARY KEY (toDoList_id),
  FOREIGN KEY (user_id) REFERENCES user(user_id)
);


CREATE TABLE group_user
(
  group_id INT NOT NULL,
  user_id INT NOT NULL,
  PRIMARY KEY (group_id, user_id),
  FOREIGN KEY (group_id) REFERENCES `group`(group_id),
  FOREIGN KEY (user_id) REFERENCES `user`(user_id)
);

CREATE TABLE resource_toDoList
(
  resource_id INT NOT NULL,
  toDoList_id INT NOT NULL,
  PRIMARY KEY (resource_id, toDoList_id),
  FOREIGN KEY (resource_id) REFERENCES resource(resource_id),
  FOREIGN KEY (toDoList_id) REFERENCES toDoList(toDoList_id)
);
