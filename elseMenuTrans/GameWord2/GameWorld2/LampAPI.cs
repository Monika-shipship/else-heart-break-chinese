using System;
using ProgrammingLanguageNr1;
using TingTing;

namespace GameWorld2
{
	// Token: 0x02000051 RID: 81
	public class LampAPI
	{
		// Token: 0x0600053F RID: 1343 RVA: 0x0001983C File Offset: 0x00017A3C
		public LampAPI(Computer pComputer, TingRunner pTingRunner)
		{
			this._computer = pComputer;
			this._tingRunner = pTingRunner;
		}

		// Token: 0x06000540 RID: 1344 RVA: 0x00019854 File Offset: 0x00017A54
		[SprakAPI(new string[] { "Turn off a lamp" })]
		public void API_TurnOff(string lampName)
		{
			Lamp lamp = this.GetLamp(lampName);
			if (lamp != null)
			{
				lamp.on = false;
				this._computer.API_Print("'" + lampName + "' was turned off");
			}
			else
			{
				this._computer.API_Print("Can't find a lamp named '" + lampName + "'");
			}
		}

		// Token: 0x06000541 RID: 1345 RVA: 0x000198B4 File Offset: 0x00017AB4
		[SprakAPI(new string[] { "Turn on a lamp" })]
		public void API_TurnOn(string lampName)
		{
			Lamp lamp = this.GetLamp(lampName);
			if (lamp != null)
			{
				lamp.on = true;
				this._computer.API_Print("'" + lampName + "' was turned on");
			}
			else
			{
				this._computer.API_Print("Can't find a lamp named '" + lampName + "'");
			}
		}

		// Token: 0x06000542 RID: 1346 RVA: 0x00019914 File Offset: 0x00017B14
		[SprakAPI(new string[] { "Flip the switch on a lamp" })]
		public void API_Switch(string lampName)
		{
			Lamp lamp = this.GetLamp(lampName);
			if (lamp != null)
			{
				if (lamp.on)
				{
					lamp.on = false;
					this._computer.API_Print("'" + lampName + "' was switched off");
				}
				else
				{
					lamp.on = true;
					this._computer.API_Print("'" + lampName + "' was switched on");
				}
			}
			else
			{
				this._computer.API_Print("Can't find a lamp named '" + lampName + "'");
			}
		}

		// Token: 0x06000543 RID: 1347 RVA: 0x000199A4 File Offset: 0x00017BA4
		private Lamp GetLamp(string lampName)
		{
			return this._tingRunner.GetTingUnsafe(lampName) as Lamp;
		}

		// Token: 0x04000159 RID: 345
		private Computer _computer;

		// Token: 0x0400015A RID: 346
		private TingRunner _tingRunner;
	}
}
