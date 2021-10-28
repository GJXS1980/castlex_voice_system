/*
* 语音合成（Text To Speech，TTS）技术能够自动将任意文字实时转换为连续的
* 自然语音，是一种能够在任何时间、任何地点，向任何人提供语音信息服务的
* 高效便捷手段，非常符合信息时代海量数据、动态更新和个性化查询的需求。
*/

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>

#include "qtts.h"
#include "msp_cmn.h"
#include "msp_errors.h"

#include "ros/ros.h"
#include "std_msgs/String.h"
#include <std_msgs/Int32.h>

using namespace std;

// const char* fileName = "./voice.wav" ;
// const char* playPath = "play ./voice.wav" ;
string appid;
string speech_param;
ros::Publisher pub;
ros::Publisher asr_pub;
string fileName_path;
string playPath_path;
string fileName;
string playPath;

/* wav音频头部格式 */
typedef struct _wave_pcm_hdr
{
	char            riff[4];                // = "RIFF"
	int		size_8;                 // = FileSize - 8
	char            wave[4];                // = "WAVE"
	char            fmt[4];                 // = "fmt "
	int		fmt_size;		// = 下一个结构体的大小 : 16

	short int       format_tag;             // = PCM : 1
	short int       channels;               // = 通道数 : 1
	int		samples_per_sec;        // = 采样率 : 8000 | 6000 | 11025 | 16000
	int		avg_bytes_per_sec;      // = 每秒字节数 : samples_per_sec * bits_per_sample / 8
	short int       block_align;            // = 每采样点字节数 : wBitsPerSample / 8
	short int       bits_per_sample;        // = 量化比特数: 8 | 16

	char            data[4];                // = "data";
	int		data_size;              // = 纯数据长度 : FileSize - 44 
} wave_pcm_hdr;

/* 默认wav音频头部数据 */
wave_pcm_hdr default_wav_hdr = 
{
	{ 'R', 'I', 'F', 'F' },
	0,
	{'W', 'A', 'V', 'E'},
	{'f', 'm', 't', ' '},
	16,
	1,
	1,
	16000,
	32000,
	2,
	16,
	{'d', 'a', 't', 'a'},
	0  
};

//获取wav文件播放时间
// 单位：秒
double get_wav_time_length(const char* filename)
{
	double len = 0.0;
 
	if (filename != NULL)
	{
		FILE* fp;
		fp = fopen(filename, "rb");
		if (fp != NULL)
		{
			int i;
			int j;
			fseek(fp, 28, SEEK_SET);
			fread(&i, sizeof(i), 1, fp);
			fseek(fp, 40, SEEK_SET);
			fread(&j, sizeof(j), 1, fp);		
 
			fclose(fp);
			fp = NULL;
 
			len = (double)j/(double)i;
		}
	}
	return len;
}

/* 文本合成 */
int text_to_speech(const char* src_text, const char* des_path, const char* params)
{
	int          ret          = -1;
	FILE*        fp           = NULL;
	const char*  sessionID    = NULL;
	unsigned int audio_len    = 0;
	wave_pcm_hdr wav_hdr      = default_wav_hdr;
	int          synth_status = MSP_TTS_FLAG_STILL_HAVE_DATA;

	if (NULL == src_text || NULL == des_path)    //语音内容为空，或目的地址为空，则报错
	{
		printf("params is error!\n");
		return ret;
	}
	fp = fopen(des_path, "wb");
	if (NULL == fp)
	{
		printf("open %s error.\n", des_path);
		return ret;
	}
	/* 开始合成 */
	sessionID = QTTSSessionBegin(params, &ret);    //配置会话参数
	if (MSP_SUCCESS != ret)     //判断输入的参数是否合法
	{
		printf("QTTSSessionBegin failed, error code: %d.\n", ret);
		fclose(fp);
		return ret;
	}
	ret = QTTSTextPut(sessionID, src_text, (unsigned int)strlen(src_text), NULL);    //将会话请求内容put到云端，请求云端返回语音流文件
	if (MSP_SUCCESS != ret)
	{
		printf("QTTSTextPut failed, error code: %d.\n",ret);
		QTTSSessionEnd(sessionID, "TextPutError");
		fclose(fp);
		return ret;
	}
	printf("正在合成 ...\n");
	fwrite(&wav_hdr, sizeof(wav_hdr) ,1, fp); //添加wav音频头，使用采样率为16000
	while (1) 
	{
		/* 获取合成音频 */
		const void* data = QTTSAudioGet(sessionID, &audio_len, &synth_status, &ret);    //获取云端发送过来的语音流文件
		if (MSP_SUCCESS != ret)
			break;
		if (NULL != data)
		{
			fwrite(data, audio_len, 1, fp);
		    wav_hdr.data_size += audio_len; //计算data_size大小
		}
		if (MSP_TTS_FLAG_DATA_END == synth_status)    //语音合成完毕
			break;
		printf(">");
		usleep(150*1000); //防止频繁占用CPU
	}
	printf("\n");
	if (MSP_SUCCESS != ret)
	{
		printf("QTTSAudioGet failed, error code: %d.\n",ret);
		QTTSSessionEnd(sessionID, "AudioGetError");
		fclose(fp);
		return ret;
	}
	/* 修正wav文件头数据的大小 */
	wav_hdr.size_8 += wav_hdr.data_size + (sizeof(wav_hdr) - 8);
	
	/* 将修正过的数据写回文件头部,音频文件为wav格式 */
	fseek(fp, 4, 0);
	fwrite(&wav_hdr.size_8,sizeof(wav_hdr.size_8), 1, fp); //写入size_8的值
	fseek(fp, 40, 0); //将文件指针偏移到存储data_size值的位置
	fwrite(&wav_hdr.data_size,sizeof(wav_hdr.data_size), 1, fp); //写入data_size的值
	fclose(fp);
	fp = NULL;
	/* 合成完毕 */
	ret = QTTSSessionEnd(sessionID, "Normal");
	if (MSP_SUCCESS != ret)
	{
		printf("QTTSSessionEnd failed, error code: %d.\n",ret);
	}

	return ret;
}

void make_text_to_wav(const char* text, const char* filename)
{
	int         ret                  = MSP_SUCCESS;
	const char* login_params_1 = "appid = ";
	
	const char* login_params         = appid.data();//"appid = 5b6d44ed, work_dir = .";//登录参数,appid与msc库绑定,请勿随意改动
	/*
	* rdn:           合成音频数字发音方式
	* volume:        合成音频的音量
	* pitch:         合成音频的音调
	* speed:         合成音频对应的语速
	* voice_name:    合成发音人
	* sample_rate:   合成音频采样率
	* text_encoding: 合成文本编码格式
	*
	*/
	const char* session_begin_params = speech_param.data();//"voice_name = nannan, text_encoding = utf8, sample_rate = 16000, speed = 50, volume = 50, pitch = 50, rdn = 2";

	/* 用户登录 */
	ret = MSPLogin(NULL, NULL, login_params);//第一个参数是用户名，第二个参数是密码，第三个参数是登录参数，用户名和密码可在http://www.xfyun.cn注册获取
	if (MSP_SUCCESS != ret)
	{
		printf("MSPLogin failed, error code: %d.\n", ret);
		goto exit ;//登录失败，退出登录
	}
	printf("开始合成 ...\n");
	ret = text_to_speech(text, filename, session_begin_params);
	if (MSP_SUCCESS != ret)
	{
		printf("text_to_speech failed, error code: %d.\n", ret);
	}
	printf("合成完毕\n");

exit:
	printf("按任意键退出 ...\n");
	//getchar();
	MSPLogout(); //退出登录

}

void playWav()
{
	//printf("~~~~~~~~~~~~~~~~~~~");
	//printf("%f\n\r",get_wav_time_length(fileName)); //获取音频长度
	std_msgs::Int32 msg;
	msg.data = 0;    //告诉ASR节点音频准备播放，避免冲突
	pub.publish(msg);

	ros::NodeHandle nh("~");    //用于launch文件传递参数
	nh.param("playPath_path", playPath_path, std::string("play ./voice.wav"));    //从launch文件获取参数
	const char *playPath = playPath_path.data();

	system(playPath);
	//播放完成
	//msg.data = 1;    //告诉ASR节点音频播放完成，避免冲突
	//pub.publish(msg);
	//asr_pub.publish(msg); //在播放一段音频后发送语音唤醒topic，对话时不需要多次唤醒
}

void xfCallBack(const std_msgs::String::ConstPtr& msg)
{
	std::cout<<"get topic text:"<< msg->data.c_str()<<std::endl;

	ros::NodeHandle nh("~");    //用于launch文件传递参数
	nh.param("fileName_path", fileName_path, std::string("./voice.wav"));    //从launch文件获取参数
	const char *fileName = fileName_path.data();

	make_text_to_wav(msg->data.c_str(), fileName);
    //tts_flag = true;
	playWav();
}
/*
void orderCallBack(const std_msgs::Int32::ConstPtr& msg)
{
	order_flag = true;
}
*/
int main(int argc, char* argv[])
{
	bool order_flag = false;
	bool tts_flag = false;
	ros::init(argc, argv, "castle_tts_node");    //初始化节点，节点名为"castle_xf_tts_node"
	ros::NodeHandle n;
	ros::NodeHandle nh("~");    //用于launch文件传递参数
	nh.param("appid", appid, string("appid = 551d49a3, work_dir = ."));    //从launch文件获取参数

	nh.param("fileName_path", fileName_path, std::string("./voice.wav"));    //从launch文件获取参数
	nh.param("playPath_path", playPath_path, std::string("play ./voice.wav"));    //从launch文件获取参数

	const char *fileName = fileName_path.data();
	const char *playPath = playPath_path.data();

	ros::Subscriber sub = n.subscribe("/voice/castle_nlu_topic", 3, xfCallBack);    //	订阅语义理解话题
	//ros::Subscriber sub2 = n.subscribe("/voice/castle_order_topic",orderCallBack);    //命令词识别失败时进行语音交互
	pub = n.advertise<std_msgs::Int32>("/voice/castle_tts_topic", 1); 		//	发布语音合成话题
	//asr_pub = n.advertise<std_msgs::Int32>("/voice/castle_awake_topic", 1);  //	发布语音唤醒数据话题
	nh.param("speech_param", speech_param, string("voice_name = nannan, text_encoding = utf8, sample_rate = 16000, speed = 50, volume = 50, pitch = 50, rdn = 0"));

	const char* start = "您好，我是广州慧谷Castle-X机器人";
	make_text_to_wav(start, fileName);
	playWav();
	ros::Rate loop_rate(1);    //10Hz循环周期
	while(ros::ok())
	{
		/*
		if order_flag && tts_flag
		{
			playWav()
			order_flag = false
			tts_flag = false
		}
		*/
		loop_rate.sleep();
		ros::spinOnce();
	}
	return 0;
}

