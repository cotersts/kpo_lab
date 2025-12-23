Feature: Товары (Products)
  CRUD и валидации SKU/удаления

  Scenario: Создать товар успешно
    Given чистое API
    When я отправляю POST "/api/products" с JSON: {"sku":"TV-42-001","name":"Телевизор Samsung 43'","category":"TV","price":39990.0}
    Then статус ответа = 201
    And в ответе JSON поле "id" существует
    And в ответе JSON поле "sku" = "TV-42-001"

  Scenario: Нельзя создать товар с уже существующим SKU
    Given чистое API
    And существует товар с SKU DUP-001
    When я отправляю POST "/api/products" с JSON: {"sku":"DUP-001","name":"Дубликат","category":"TV","price":1000.0}
    Then статус ответа = 400
    And в ответе detail содержит "уже существует"

  Scenario: Поиск товара по q
    Given чистое API
    And существует товар с SKU SEARCH-ABC
    When я отправляю GET "/api/products?q=SEARCH"
    Then статус ответа = 200

  Scenario: Обновить товар (PATCH) успешно
    Given чистое API
    And существует товар с SKU UPD-001
    When я отправляю GET "/api/products?q=UPD-001"
    Then статус ответа = 200
    When я отправляю PATCH "/api/products/1" с JSON: {"price":12345.67}
    Then статус ответа = 200
    And в ответе JSON поле "price" = 12345.670000

  Scenario: Нельзя удалить товар, который используется в продажах
    Given чистое API
    And существует товар и клиент и продажа на этот товар
    When я отправляю DELETE "/api/products/1"
    Then статус ответа = 400
    And в ответе detail содержит "используется в продажах"
