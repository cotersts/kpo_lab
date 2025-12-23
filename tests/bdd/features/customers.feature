Feature: Клиенты (Customers)
  Создание и уникальность email

  Scenario: Создать клиента успешно
    Given чистое API
    When я отправляю POST "/api/customers" с JSON: {"name":"Иван Петров","phone":"+7-900-000-00-00","email":"ivan@example.com"}
    Then статус ответа = 201
    And в ответе JSON поле "id" существует
    And в ответе JSON поле "email" = "ivan@example.com"

  Scenario: Нельзя создать клиента с тем же email
    Given чистое API
    And существует клиент с email dup@example.com
    When я отправляю POST "/api/customers" с JSON: {"name":"Другой","phone":"+7-900-000-00-01","email":"dup@example.com"}
    Then статус ответа = 400
    And в ответе detail содержит "уже существует"

  Scenario: Получить список клиентов
    Given чистое API
    When я отправляю GET "/api/customers"
    Then статус ответа = 200
