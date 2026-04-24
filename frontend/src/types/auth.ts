export interface GA4Property {
  id: string;
  name: string;
}

export interface GA4Account {
  id: string;
  name: string;
  properties: GA4Property[];
}

export interface AppSession {
  sessionId: string;
  propertyId: string;
  propertyName: string;
  accountName: string;
}