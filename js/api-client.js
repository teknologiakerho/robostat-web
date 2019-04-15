function encodeQuery(params){
	if(!params)
		return "";

	const ret = [];

	for(let p in params){
		const val = params[p];
		if(val === false || val === undefined)
			continue;

		if(Array.isArray(val)){
			for(let v of val)
				ret.push(`${p}=${encodeURIComponent(v)}`);
		}else{
			ret.push(`${p}=${encodeURIComponent(val)}`);
		}
	}

	return ret.join("&");
}

export class ApiClient {

	constructor(api){
		this.api = api.replace(/\/+$/, "");
	}

	async request(path, params, init){
		const resp = await fetch(`${this.api}${path}?${encodeQuery(params)}`, init);

		if(!resp.ok){
			const text = await resp.text();
			let error;

			try {
				error = JSON.parse(text).error;
			} catch(e) {
				error = `${resp.status} ${resp.statusText}: ${text}`;
			}

			throw error;
		}

		return await resp.json();
	}

	async postJson(path, params, data){
		return await this.request(path, params, {
			method: "POST",
			headers: new Headers({
				"Content-Type": "application/json"
			}),
			body: JSON.stringify(data)
		});
	}

}
