export interface FlagData {
  id?: number;
  sploit: string;
  flag: string;
  team: string;
  status: string;
  checksystem_response?: string;
  time: number;
}

export class Flag {
  id?: number;
  sploit: string;
  flag: string;
  team: string;
  status: string;
  checksystemResponse: string;
  time: number;

  constructor({
    id,
    sploit,
    flag,
    team,
    status,
    checksystem_response: checksystemResponse = '',
    time,
  }: FlagData) {
    this.id = id;
    this.sploit = sploit;
    this.flag = flag;
    this.team = team;
    this.status = status;
    this.checksystemResponse = checksystemResponse || '';
    this.time = time;
  }
}
