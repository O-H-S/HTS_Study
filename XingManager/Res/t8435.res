BEGIN_FUNCTION_MAP
	.Func,파생종목마스터조회API용(t8435),t8435,block,headtype=A;
	BEGIN_DATA_MAP
	t8435InBlock,기본입력,input;
	begin
		구분(MF/MO),gubun,gubun,char,2;
	end
	t8435OutBlock,파생종목마스터,output,occurs;
	begin
		종목명,hname,hname,char,20;
		단축코드,shcode,shcode,char,8;
		확장코드,expcode,expcode,char,12;
		상한가,uplmtprice,uplmtprice,float,6.2;
		하한가,dnlmtprice,dnlmtprice,float,6.2;
		전일종가,jnilclose,jnilclose,float,6.2;
		전일고가,jnilhigh,jnilhigh,float,6.2;
		전일저가,jnillow,jnillow,float,6.2;
		기준가,recprice,recprice,float,6.2;
	end
	END_DATA_MAP
END_FUNCTION_MAP

