using System;
using GameTypes;
using GrimmLib;
using ProgrammingLanguageNr1;
using TingTing;

namespace GameWorld2
{
	// Token: 0x02000058 RID: 88
	public class HeartAPI
	{
		// Token: 0x0600056E RID: 1390 RVA: 0x0001ACE4 File Offset: 0x00018EE4
		public HeartAPI(Computer pComputer, TingRunner pTingRunner, DialogueRunner pDialogueRunner)
		{
			this._computer = pComputer;
			this._tingRunner = pTingRunner;
			this._dialogueRunner = pDialogueRunner;
		}

		// Token: 0x06000570 RID: 1392 RVA: 0x0001AD3C File Offset: 0x00018F3C
		[SprakAPI(new string[] { "Set numeric data on object" })]
		public void API_SetNumericData(string objectName, string dataName, float value)
		{
			Ting tingUnsafe = this._tingRunner.GetTingUnsafe(objectName);
			if (tingUnsafe == null)
			{
				this._computer.API_Print("Can't find object with name \"" + objectName + "\"");
				return;
			}
			tingUnsafe.table.SetValue<float>(tingUnsafe.objectId, dataName, value);
			this._computer.API_Print(string.Concat(new object[] { "Set ", dataName, " to ", value, " on ", objectName }));
		}

		// Token: 0x06000571 RID: 1393 RVA: 0x0001ADCC File Offset: 0x00018FCC
		[SprakAPI(new string[] { "Get numeric data on object" })]
		public float API_GetNumericData(string objectName, string dataName)
		{
			Ting tingUnsafe = this._tingRunner.GetTingUnsafe(objectName);
			if (tingUnsafe == null)
			{
				this._computer.API_Print("Can't find object with name \"" + objectName + "\"");
				return 0f;
			}
			return tingUnsafe.table.GetValue<float>(tingUnsafe.objectId, dataName);
		}

		// Token: 0x06000572 RID: 1394 RVA: 0x0001AE24 File Offset: 0x00019024
		[SprakAPI(new string[] { "Break" })]
		public void API_Break()
		{
			this._computer.masterProgram.sourceCodeContent = "a00j ksdhg 245kljshg a sl3434 kjghklj434 651 xsdhgkl";
			this._computer.masterProgram.sourceCodeName = "";
			throw new Error("BROKEN", Error.ErrorType.RUNTIME, -1, -1);
		}

		// Token: 0x06000573 RID: 1395 RVA: 0x0001AE68 File Offset: 0x00019068
		[SprakAPI(new string[] { "" })]
		public void API_ZapPersonGently(string name)
		{
			Character character = this._tingRunner.GetTingUnsafe(name) as Character;
			if (character == null)
			{
				throw new Error("Can't find " + name);
			}
			character.StopAction();
			character.GetTasedGently();
			if (Randomizer.OneIn(3))
			{
				character.Say(Randomizer.RandNth<string>(HeartAPI.zapExclaims), "Misc");
			}
		}

		// Token: 0x0400016C RID: 364
		private Computer _computer;

		// Token: 0x0400016D RID: 365
		private TingRunner _tingRunner;

		// Token: 0x0400016E RID: 366
		private DialogueRunner _dialogueRunner;

		// Token: 0x0400016F RID: 367
		private static string[] zapExclaims = new string[] { "Ahhhh!!!", "AAAA!!!", "OOHH", "UUUUuuuu", "!!!" };
	}
}
