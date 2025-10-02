export interface TeamData {
  name: string;
  address: string;
}

export class Team {
  name: string;
  address: string;

  constructor({ name, address }: TeamData) {
    this.name = name;
    this.address = address;
  }
}
