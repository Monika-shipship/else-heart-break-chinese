using System;
using System.Collections.Generic;
using GameTypes;
using ProgrammingLanguageNr1;
using RelayLib;
using TingTing;

namespace GameWorld2
{
	// Token: 0x02000023 RID: 35
	public class Lamp : MimanTing
	{
		// Token: 0x06000316 RID: 790 RVA: 0x00012268 File Offset: 0x00010468
		public override bool DoesMasterProgramExist()
		{
			return this._program != null;
		}

		// Token: 0x06000317 RID: 791 RVA: 0x00012278 File Offset: 0x00010478
		protected override void SetupCells()
		{
			base.SetupCells();
			this.CELL_programName = base.EnsureCell<string>("masterProgramName", "StreetLight");
			this.CELL_color = base.EnsureCell<Float3>("color", new Float3(0f, 0f, 0f));
			this.CELL_on = base.EnsureCell<bool>("on", true);
		}

		// Token: 0x06000318 RID: 792 RVA: 0x000122D8 File Offset: 0x000104D8
		public override void MaybeFixGroupIfOutsideIslandOfTiles()
		{
			base.FixGroupIfOutsideIslandOfTiles();
		}

		// Token: 0x06000319 RID: 793 RVA: 0x000122E0 File Offset: 0x000104E0
		public override void Update(float dt)
		{
			base.UpdateBubbleTimer();
		}

		// Token: 0x0600031A RID: 794 RVA: 0x000122E8 File Offset: 0x000104E8
		[SprakAPI(new string[] { "Set the color of the lamp", "red", "green", "blue" })]
		public void API_SetColor(float r, float g, float b)
		{
			this.logger.Log(string.Concat(new object[] { "Called API_SetColor with arguments ", r, ", ", g, ", ", b }));
			this.color = new Float3(r, g, b);
		}

		// Token: 0x0600031B RID: 795 RVA: 0x0001234C File Offset: 0x0001054C
		[SprakAPI(new string[] { "Returns true if it is night" })]
		public bool API_IsNight()
		{
			return base.gameClock.hours > 18 || base.gameClock.hours < 6;
		}

		// Token: 0x0600031C RID: 796 RVA: 0x00012384 File Offset: 0x00010584
		[SprakAPI(new string[] { "Returns a random value between 0.0 and 1.0" })]
		public float API_Random()
		{
			return (float)Lamp.s_random.NextDouble();
		}

		// Token: 0x0600031D RID: 797 RVA: 0x00012394 File Offset: 0x00010594
		[SprakAPI(new string[] { "Returns the time since day 0, whatever that means (in seconds)" })]
		public float API_Time()
		{
			return base.gameClock.totalSeconds;
		}

		// Token: 0x0600031E RID: 798 RVA: 0x000123B0 File Offset: 0x000105B0
		[SprakAPI(new string[] { "The sinus function", "x" })]
		public float API_Sin(float x)
		{
			return (float)Math.Sin((double)x);
		}

		// Token: 0x0600031F RID: 799 RVA: 0x000123BC File Offset: 0x000105BC
		[SprakAPI(new string[] { "Say something" })]
		public void API_Say(string text)
		{
			this.Say(text, "");
		}

		// Token: 0x06000320 RID: 800 RVA: 0x000123CC File Offset: 0x000105CC
		[SprakAPI(new string[] { "Pause the master program", "number of seconds to pause for" })]
		public void API_Sleep(float seconds)
		{
			this.masterProgram.sleepTimer = seconds;
		}

		// Token: 0x06000321 RID: 801 RVA: 0x000123DC File Offset: 0x000105DC
		[SprakAPI(new string[] { "Turn on the lamp", "" })]
		public void API_TurnOn()
		{
			this.on = true;
		}

		// Token: 0x06000322 RID: 802 RVA: 0x000123E8 File Offset: 0x000105E8
		[SprakAPI(new string[] { "Turn off the lamp", "" })]
		public void API_TurnOff()
		{
			this.on = false;
		}

		// Token: 0x06000323 RID: 803 RVA: 0x000123F4 File Offset: 0x000105F4
		[SprakAPI(new string[] { "Play a sound", "name" })]
		public void API_PlaySound(string name)
		{
			base.PlaySound(name);
			base.audioLoop = false;
		}

		// Token: 0x06000324 RID: 804 RVA: 0x00012404 File Offset: 0x00010604
		public void Kick()
		{
			this.masterProgram.Start();
			this._dialogueRunner.EventHappened("LampWasKicked");
		}

		// Token: 0x170000B8 RID: 184
		// (get) Token: 0x06000325 RID: 805 RVA: 0x00012424 File Offset: 0x00010624
		public override bool canBePickedUp
		{
			get
			{
				return false;
			}
		}

		// Token: 0x170000B9 RID: 185
		// (get) Token: 0x06000326 RID: 806 RVA: 0x00012428 File Offset: 0x00010628
		public override string verbDescription
		{
			get
			{
				return "kick";
			}
		}

		// Token: 0x170000BA RID: 186
		// (get) Token: 0x06000327 RID: 807 RVA: 0x00012430 File Offset: 0x00010630
		public override string tooltipName
		{
			get
			{
				return "lamp";
			}
		}

		// Token: 0x170000BB RID: 187
		// (get) Token: 0x06000328 RID: 808 RVA: 0x00012438 File Offset: 0x00010638
		// (set) Token: 0x06000329 RID: 809 RVA: 0x00012448 File Offset: 0x00010648
		[ShowInEditor]
		public Float3 color
		{
			get
			{
				return this.CELL_color.data;
			}
			set
			{
				this.CELL_color.data = value;
			}
		}

		// Token: 0x170000BC RID: 188
		// (get) Token: 0x0600032A RID: 810 RVA: 0x00012458 File Offset: 0x00010658
		// (set) Token: 0x0600032B RID: 811 RVA: 0x00012468 File Offset: 0x00010668
		[EditableInEditor]
		public bool on
		{
			get
			{
				return this.CELL_on.data;
			}
			set
			{
				this.CELL_on.data = value;
			}
		}

		// Token: 0x170000BD RID: 189
		// (get) Token: 0x0600032C RID: 812 RVA: 0x00012478 File Offset: 0x00010678
		// (set) Token: 0x0600032D RID: 813 RVA: 0x00012488 File Offset: 0x00010688
		[EditableInEditor]
		public string masterProgramName
		{
			get
			{
				return this.CELL_programName.data;
			}
			set
			{
				this.CELL_programName.data = value;
			}
		}

		// Token: 0x170000BE RID: 190
		// (get) Token: 0x0600032E RID: 814 RVA: 0x00012498 File Offset: 0x00010698
		public override Program masterProgram
		{
			get
			{
				if (this._program == null)
				{
					this._program = base.EnsureProgram("MasterProgram", this.masterProgramName);
					this._program.FunctionDefinitions = new List<FunctionDefinition>(FunctionDefinitionCreator.CreateDefinitions(this, typeof(Lamp)));
				}
				return this._program;
			}
		}

		// Token: 0x0600032F RID: 815 RVA: 0x000124F0 File Offset: 0x000106F0
		public override void PrepareForBeingHacked()
		{
			if (this.masterProgram == null)
			{
				this.logger.Log("There was a problem generating the master program");
			}
			else
			{
				this.masterProgram.nameOfOwner = base.name;
			}
		}

		// Token: 0x040000C7 RID: 199
		public new static string TABLE_NAME = "Ting_Lamps";

		// Token: 0x040000C8 RID: 200
		private ValueEntry<string> CELL_programName;

		// Token: 0x040000C9 RID: 201
		private ValueEntry<Float3> CELL_color;

		// Token: 0x040000CA RID: 202
		private ValueEntry<bool> CELL_on;

		// Token: 0x040000CB RID: 203
		private Program _program;

		// Token: 0x040000CC RID: 204
		private static Random s_random = new Random(DateTime.Today.Millisecond * DateTime.Today.Second * DateTime.Today.Minute * DateTime.Today.Hour);
	}
}
