# openapi-android-client

## Requirements

Building the API client library requires [Maven](https://maven.apache.org/) to be installed.

## Installation

To install the API client library to your local Maven repository, simply execute:

```shell
mvn install
```

To deploy it to a remote Maven repository instead, configure the settings of the repository and execute:

```shell
mvn deploy
```

Refer to the [official documentation](https://maven.apache.org/plugins/maven-deploy-plugin/usage.html) for more information.

### Maven users

Add this dependency to your project's POM:

```xml
<dependency>
    <groupId>org.openapitools</groupId>
    <artifactId>openapi-android-client</artifactId>
    <version>1.0.0</version>
    <scope>compile</scope>
</dependency>
```

### Gradle users

Add this dependency to your project's build file:

```groovy
compile "org.openapitools:openapi-android-client:1.0.0"
```

### Others

At first generate the JAR by executing:

    mvn package

Then manually install the following JARs:

- target/openapi-android-client-1.0.0.jar
- target/lib/*.jar

## Getting Started

Please follow the [installation](#installation) instruction and execute the following Java code:

```java

import org.openapitools.client.api.DefaultApi;

public class DefaultApiExample {

    public static void main(String[] args) {
        DefaultApi apiInstance = new DefaultApi();
        String description = null; // String | 
        String material = null; // String | 
        String color = null; // String | 
        BigDecimal width = null; // BigDecimal | X axis (mm)
        BigDecimal length = null; // BigDecimal | Y axis (mm)
        BigDecimal height = null; // BigDecimal | Z axis (mm)
        BigDecimal infill = null; // BigDecimal | Infill % (0-100)
        BigDecimal realWeight = null; // BigDecimal | W (grams)
        File file = null; // File | 
        try {
            CreateOrderPost200Response result = apiInstance.createOrderPost(description, material, color, width, length, height, infill, realWeight, file);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling DefaultApi#createOrderPost");
            e.printStackTrace();
        }
    }
}

```

## Documentation for API Endpoints

All URIs are relative to *http://localhost:8000*

Class | Method | HTTP request | Description
------------ | ------------- | ------------- | -------------
*DefaultApi* | [**createOrderPost**](docs/DefaultApi.md#createOrderPost) | **POST** /create_order | Create 3D printing order with advanced price calculation
*DefaultApi* | [**loginPost**](docs/DefaultApi.md#loginPost) | **POST** /login | Login user
*DefaultApi* | [**meGet**](docs/DefaultApi.md#meGet) | **GET** /me | Get current user info
*DefaultApi* | [**ordersGet**](docs/DefaultApi.md#ordersGet) | **GET** /orders | Get list of user orders
*DefaultApi* | [**registerPost**](docs/DefaultApi.md#registerPost) | **POST** /register | Register new user
*DefaultApi* | [**resendVerificationPost**](docs/DefaultApi.md#resendVerificationPost) | **POST** /resend-verification | Resend email verification link


## Documentation for Models

 - [CreateOrderPost200Response](docs/CreateOrderPost200Response.md)


## Documentation for Authorization

Authentication schemes defined for the API:
### bearerAuth

- **Type**: HTTP Bearer Token authentication (JWT)


## Recommendation

It's recommended to create an instance of `ApiClient` per thread in a multithreaded environment to avoid any potential issues.

## Author



