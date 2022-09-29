#include <ros/ros.h>
#include <std_msgs/String.h>
#include <sstream>
#include <jsoncpp/json/json.h>
#include <curl/curl.h>
#include <string>
#include <exception>

#include "std_msgs/Int64.h"

using namespace std;

int flag = 0;
string result;
string tuling_key; //default tuling key
string userid;

int writer(char *data, size_t size, size_t nmemb, string *writerData)
{
     if (writerData == NULL)
     {
         return -1;
     }
     
     int len = size*nmemb;
     writerData->append(data, len);
     return len;
}


/**
 * parse tuling server response json string
 */
int parseJsonResonse(string input)    //由返回的json数据解析出text文本
{
    Json::Value root;
    Json::Reader reader;
    cout << "tuling server response origin json str:" << input << endl;
    bool parsingSuccessful = reader.parse(input, root);

    if(!parsingSuccessful)
    {
        cout << "!!! Failed to parse the response data" <<endl;
        return 1;
    }

/**
{
    "intent":{
        "appKey":
            "platform.weather",
            "code":0,
            "operateState":1100,
            "parameters":{
                "date":"",
                "city":"广州"
                }
            },
        "results":
            [
                {
                    "groupType":0,
                    "resultType":"text",
                    "values":{
                    "text":"广州:周四 09月29日,多云 持续无风向,最低气温25度，最高气温34度。"
                    }
                }
            ]
}

 */

    // int file_size = root["results"].size();
    // for(int i = 0; i < file_size; ++i) 
    // {  
    //   Json::Value val_image = root["files"][i]["images"];  
    //   int image_size = val_image.size();  
    //   for(int j = 0; j < image_size; ++j)  
    //   {  
    //     std::string type = val_image[j]["type"].asString();  
    //     std::string url = val_image[j]["url"].asString();  
    //   }  
    // }

    const Json::Value code = root["intent"]["code"];    //root是取出code对应的值
    const Json::Value text = root["results"][0]["values"]["text"];
    result = text.asString();
    flag = 1;
    cout << "response code:" << code << endl;
    cout << "response results:" << result <<endl;

    return 0;
}


/**
 * send tuling server http pose requeset
 */
int HttpPostRequest(string input, string key)
{
    string buffer;
/*
{            
“key”: “APIKEY”,              
“info”: “今天天气怎么样”,
"userid": "HGcastle"   
}

{
        "reqType": 0,
        "perception": {
            "inputText": {
                "text": question
            }
        },
        "userInfo": {
            "apiKey": "14daac8ca27b4170a46d8f0ea1d29d88",
            "userId": "1234"
        }
    }

*/
    std::string strJson = "{";
    strJson += "\"reqType\" : 0,";
    strJson += "\"perception\" : {";
    strJson += "\"inputText\" : {";
    strJson += "\"text\" : ";
    strJson += "\"";
    strJson += input;
    strJson += "\"";
    strJson += "}";
    strJson += "},";
    strJson += "\"userInfo\" : {";
    strJson += "\"apiKey\" : ";
    strJson += "\"";
    strJson += key;
    strJson += "\",";
    strJson += "\"userId\" : ";
    strJson += "\"";
    strJson += userid;
    strJson += "\"";
    strJson += "}";
    strJson += "}";

    cout<< "post json string:" << strJson <<endl;
    try
    {
        //调用Curl向图灵发送请求
        CURL *pCurl = NULL;    //定义空的curl空指针
        CURLcode res;    //返回声明码，用来检测是否返回成功
        curl_global_init(CURL_GLOBAL_ALL);    //初始化curl

        // get a curl handle
        pCurl = curl_easy_init();    //获取curl句柄
        if (NULL != pCurl)
        {
            //set url timeout
            curl_easy_setopt(pCurl, CURLOPT_TIMEOUT, 5);    //设置接受超时时间

            // First set the URL that is about to receive our POST.
            curl_easy_setopt(pCurl, CURLOPT_URL, "http://openapi.tuling123.com/openapi/api/v2");    //设置接口地址，注意图灵Ｖ1和V2的接口地址不一样

            // set curl http header
            curl_slist *plist = curl_slist_append(NULL,"Content-Type:application/json; charset=UTF-8");    //将json格式及utf-8编码方式放置到消息首
            curl_easy_setopt(pCurl, CURLOPT_HTTPHEADER, plist);    //将内容放到待传送消息

            // set curl post content fileds
            curl_easy_setopt(pCurl, CURLOPT_POSTFIELDS, strJson.c_str());

            curl_easy_setopt(pCurl, CURLOPT_WRITEFUNCTION, writer);    //将图灵返回的消息写到缓冲区，返回的数据实际也是json格式的消息
            curl_easy_setopt(pCurl, CURLOPT_WRITEDATA, &buffer);

            // Perform the request, res will get the return code
            res = curl_easy_perform(pCurl);    //执行请求，根据返回码检验是否返回成功

            // Check for errors
            if (res != CURLE_OK)
            {
                printf("curl_easy_perform() failed:%s\n", curl_easy_strerror(res));
            }
            // always cleanup
            curl_easy_cleanup(pCurl);    //清空curl
        }
        curl_global_cleanup();
    }
    catch (std::exception &ex)
    {
        printf("!!! curl exception %s.\n", ex.what());
    }

    if(buffer.empty())
    {
        cout << "!!! ERROR The TuLing server response NULL" <<endl;
    }
    else
    {
        parseJsonResonse(buffer);    //由json格式消息中解析出text
    }

    return 0;
}


/**
*   when nlp node get input,will auto send http post request to tuling server
**/
void nluCallback(const std_msgs::String::ConstPtr& msg)
{
    std::cout<<"我:" << msg->data << std::endl;
    HttpPostRequest(msg->data, tuling_key);
}

/**
 * main function
 */
int main(int argc, char **argv)
{
    std_msgs::Int64 tag;

    ros::init(argc, argv, "castlex_tl_nlu_node");    //初始化节点
    ros::NodeHandle n;

    std::string nlu_topic="/voice/castlex_asr_topic";    //定义语音识别的话题名称
    std::string tts_topic="/voice/castlex_nlu_topic";    //定义图灵发布的话题名称，与讯飞tts订阅话题相同

    ros::NodeHandle nh("~");    //用于launch文件传递参数
    //nh.param("tuling_key", tuling_key, string("0dd3488916f64d4eb3356308c7c20823"));
    nh.param("tuling_key", tuling_key, string("552c0addb08d4c73ab85868c2e68b22d"));
    nh.param("userid", userid, string("HGcastle"));

    ros::Subscriber sub = n.subscribe(nlu_topic, 10, nluCallback);    //实例化订阅节点，指定回调函数
    ros::Publisher pub = n.advertise<std_msgs::String>(tts_topic, 10);    //实例化发布节点，指定发布的主题及消息类型

    //ros::Publisher tts_pub = n.advertise<std_msgs::Int64>("tts_success", 1000);


    ros::Rate loop_rate(10);

    while(ros::ok())
    {
        if(flag)    //当接受到图灵云端返回的字符串应答，则将该字符串包装成消息发布给讯飞tts
        {
           std_msgs::String msg;
           msg.data = result;
           pub.publish(msg);

            tag.data = 3;
            //tts_pub.publish(tag);

           flag = 0;    //图灵返回标志位复位
        }
        ros::spinOnce();
        loop_rate.sleep();
    }

    return 0;
}


