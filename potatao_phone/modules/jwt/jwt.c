#include "py/runtime.h"
#include "py/obj.h"
#include <string.h>
#include <stdio.h>
#include "mbedtls/md.h"
#include "mbedtls/base64.h"


typedef enum {
    JWT_OK = 0,
    JWT_ERR_FORMAT,
    JWT_ERR_INVALID,
    JWT_ERR_BASE64_DECODE,
    JWT_ERR_COUNT
} jwt_error_t;

static const char *JWT_ERROR_MSG[]={
    [JWT_OK] = "success!",
    [JWT_ERR_FORMAT] = "Invalid JWT format. Missing dot separators.",
    [JWT_ERR_INVALID]  = "Signature verification failed. Token tampered or invalid secret.",
    [JWT_ERR_BASE64_DECODE]  = "Base64URL decoding failed. Payload data corrupted."
};

// generate base64 url for http request
void make_base64_url(char *str){
    for (int i = 0; str[i] != '\0'; i++) {
        if (str[i] == '+') str[i] = '-';
        if (str[i] == '/') str[i] = '_';
        if (str[i] == '=') { str[i] = '\0'; break; }
    }
}


static mp_obj_t jwt_error_string(mp_obj_t status_obj) {
    int status = mp_obj_get_int(status_obj);
    if (status < 0 || status >= JWT_ERR_COUNT) {
        return mp_obj_new_str("Unknown error code.", 19);
    }
    const char *msg = JWT_ERROR_MSG[status];
    
    return mp_obj_new_str(msg, strlen(msg));
}
static MP_DEFINE_CONST_FUN_OBJ_1(jwt_error_string_obj,jwt_error_string);


// create jwt token
static mp_obj_t jwt_create_token(mp_obj_t payload_obj, mp_obj_t secret_key_obj){
   //covert micro python object to c char pointer 
   const char *payload = mp_obj_str_get_str(payload_obj);
   const char *secret_key = mp_obj_str_get_str(secret_key_obj);
   // define token header
   const char *joken_header = "{\"alg\":\"HS256\",\"typ\":\"JWT\"}"; // mention that create token by SHA256 algorhithm
   char encoded_header[128];// define token max header size
   char encoded_payload[256]; // define token max main body size
   size_t olen; // a variable that record header and main body real length
   // convert header to base64 url
   mbedtls_base64_encode((unsigned char *) encoded_header, sizeof(encoded_header),&olen,(unsigned char *)joken_header, strlen(joken_header));
   make_base64_url(encoded_header);
   // convert main body to base64 url
   mbedtls_base64_encode((unsigned char *) encoded_payload, sizeof(encoded_payload),&olen,(unsigned char *)payload, strlen(payload));
   make_base64_url(encoded_payload);
   //define token input length
   char sign_put[512];
   //combine encoded header and encoded payload together
   snprintf(sign_put, sizeof(sign_put), "%s.%s",encoded_header,encoded_payload);
   //define SHA256 encrpyted data length
   unsigned char hemc_result[32];
   //define pico 2 w encryption information object
   const mbedtls_md_info_t *encryption_info = mbedtls_md_info_from_type(MBEDTLS_MD_SHA256);
   //encrypt data by SHA256
   mbedtls_md_hmac(encryption_info,(const unsigned char *) secret_key,strlen(secret_key),(const unsigned char *) sign_put,strlen(sign_put),hemc_result);
   //encode encrypted data
   char encoded_signature[128];
   mbedtls_base64_encode((unsigned char *) encoded_signature, sizeof(encoded_signature),&olen, (const unsigned char *)hemc_result ,32);
   make_base64_url(encoded_signature);
   char jwt[1024];
   snprintf(jwt,sizeof(jwt),"%s.%s.%s",encoded_header,encoded_payload,encoded_signature);
   return mp_obj_new_str(jwt,strlen(jwt));
}

//create micro python function object
static MP_DEFINE_CONST_FUN_OBJ_2(jwt_create_token_obj,jwt_create_token);


static mp_obj_t jwt_verify_token(mp_obj_t token_obj,mp_obj_t secret_key_obj){
    //convert micropython objct to char pointer in c
    const char *token = mp_obj_str_get_str(token_obj);
    const char *secret = mp_obj_str_get_str(secret_key_obj);
    //copy token 
    char token_copy[1024];
    strncpy(token_copy,token,sizeof(token_copy) -1);
    token_copy[sizeof(token_copy) - 1] = '\0';
    //splite token to header, payload and signature
    char *header_base64 = strtok(token_copy,".");
    char *payload_base64 = strtok(NULL,".");
    char *signature_base64 = strtok(NULL,".");
    if(!header_base64 || !payload_base64 || !signature_base64){
        return mp_obj_new_str(JWT_ERROR_MSG[JWT_ERR_FORMAT],strlen(JWT_ERROR_MSG[JWT_ERR_FORMAT]));
    }
    char sign_input[512];
    snprintf(sign_input,sizeof(sign_input),"%s.%s",header_base64,payload_base64);
    unsigned char hmac_result[32];
    const mbedtls_md_info_t *md_info = mbedtls_md_info_from_type(MBEDTLS_MD_SHA256);
    mbedtls_md_hmac(md_info, (const unsigned char *)secret, strlen(secret), 
                    (const unsigned char *)sign_input, strlen(sign_input), hmac_result);

    char expected_signature[128];
    size_t olen;
    mbedtls_base64_encode((unsigned char *)expected_signature, sizeof(expected_signature), &olen, hmac_result, 32);
    make_base64_url(expected_signature);
    // compare the encryption
    if(strcmp(signature_base64,expected_signature) != 0){
        return mp_obj_new_str(JWT_ERROR_MSG[JWT_ERR_INVALID],strlen(JWT_ERROR_MSG[JWT_ERR_INVALID]));
    }
    //decrypt data
    char payload_standard_b64[256];
    strncpy(payload_standard_b64, payload_base64, sizeof(payload_standard_b64) - 1);
    payload_standard_b64[sizeof(payload_standard_b64) - 1] = '\0';
    for (int i = 0; payload_standard_b64[i] != '\0'; i++) {
        if (payload_standard_b64[i] == '-') payload_standard_b64[i] = '+';
        if (payload_standard_b64[i] == '_') payload_standard_b64[i] = '/';
    }
    unsigned char decoded_payload[256];
    if (mbedtls_base64_decode(decoded_payload, sizeof(decoded_payload), &olen, 
                             (const unsigned char *)payload_standard_b64, strlen(payload_standard_b64)) != 0) {
        const char *err_msg = "ERROR: Base64URL decoding failed. Payload data corrupted.";
        return mp_obj_new_str(err_msg, strlen(err_msg));
    }
    decoded_payload[olen] = '\0';

    return mp_obj_new_str((const char *)decoded_payload, olen);
}

static MP_DEFINE_CONST_FUN_OBJ_2(jwt_verify_token_obj,jwt_verify_token);

static const mp_rom_map_elem_t jwt_module_global_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__),     MP_ROM_QSTR(MP_QSTR_jwt) },
    { MP_ROM_QSTR(MP_QSTR_create_token), MP_ROM_PTR(&jwt_create_token_obj) },
    { MP_ROM_QSTR(MP_QSTR_verify_token), MP_ROM_PTR(&jwt_verify_token_obj) },
    { MP_ROM_QSTR(MP_QSTR_error_string), MP_ROM_PTR(&jwt_error_string_obj) },
};

static MP_DEFINE_CONST_DICT(jwt_module_globals,jwt_module_global_table);

const mp_obj_module_t jwt_module = {
    .base = {&mp_type_module},
    .globals = (mp_obj_dict_t *) &jwt_module_globals,
};

MP_REGISTER_MODULE(MP_QSTR_jwt, jwt_module);