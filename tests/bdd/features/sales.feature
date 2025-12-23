Feature: Продажи (Sales)
  Создание продажи, подсчёт total_amount и фильтр по датам

  Scenario: Создать продажу успешно и проверить total_amount
    Given чистое API
    When я отправляю POST "/api/products" с JSON: {"sku":"SALE-01","name":"Холодильник","category":"Fridge","price":30000.0}
    Then статус ответа = 201
    When я отправляю POST "/api/customers" с JSON: {"name":"Мария","phone":"8-911-123-45-67","email":"maria@example.com"}
    Then статус ответа = 201
    When я отправляю POST "/api/sales" с JSON: {"customer_id":1,"items":[{"product_id":1,"quantity":2,"unit_price":5000.0}]}
    Then статус ответа = 201
    And total_amount продажи равен 10000.0

  Scenario: Нельзя создать продажу, если клиент не найден
    Given чистое API
    When я отправляю POST "/api/sales" с JSON: {"customer_id":999,"items":[{"product_id":1,"quantity":1,"unit_price":1000.0}]}
    Then статус ответа = 404
    And в ответе detail содержит "Клиент"

  Scenario: Нельзя создать продажу, если товар не найден
    Given чистое API
    When я отправляю POST "/api/sales" с JSON: {"customer_id":null,"items":[{"product_id":999,"quantity":1,"unit_price":1000.0}]}
    Then статус ответа = 404
    And в ответе detail содержит "Товар"

  Scenario: Нельзя получить список продаж при date_from > date_to
    Given чистое API
    When я отправляю GET "/api/sales?date_from=2025-12-10&date_to=2025-12-01"
    Then статус ответа = 400
    And в ответе detail содержит "Дата начала"
